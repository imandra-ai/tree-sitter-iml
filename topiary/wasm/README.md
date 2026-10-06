# imlformat-wasm

The Topiary IML formatter compiled to WebAssembly. It runs in JavaScript hosts (browsers,
Node, and VS Code on desktop and the web) and produces the same output as `imlformat.sh`,
using the same `../queries/iml.scm`. It is built with a few workarounds for Topiary's wasm
support; see [Workarounds](#workarounds), including the one difference from the native
formatter.

```js
import { format, init } from "imlformat-wasm";

await init();                       // once; loads web-tree-sitter, the formatter and the grammar
const out = format("let   f x=x+1"); // "let f x = x + 1\n"; throws on parse errors
```

`init` loads the `.wasm` files from `dist/` next to `index.js`. If a bundler moves them,
pass `formatterWasm`, `grammarWasm` (bytes or URLs) and `treeSitter: { locateFile }` for
web-tree-sitter's own `tree-sitter.wasm`.

## Build

Requires the Rust `wasm32-unknown-unknown` target, `wasm-bindgen-cli` 0.2.100 (it must match
the version Topiary pins), and the tree-sitter CLI >= 0.26 on `PATH`:

```bash
rustup target add wasm32-unknown-unknown
cargo install wasm-bindgen-cli --version 0.2.100 --locked
make build   # -> dist/
make test    # formats ../tests/*.iml and compares with the .formatted.iml snapshots
```

## How it fits together

| Piece                              | Where it comes from                                         |
| ---------------------------------- | ----------------------------------------------------------- |
| `dist/imlformat_wasm{.js,_bg.wasm}` | `src/lib.rs` + topiary-core 0.7.3, through wasm-bindgen    |
| `dist/tree-sitter-iml.wasm`        | `grammars/iml`, regenerated at ABI 14 in `target/`          |
| `web-tree-sitter` 0.21.0 (npm)      | Does the parsing; topiary-core calls into it on wasm32     |

## Workarounds

Topiary's wasm support is not built or tested in its releases, so this build needs four
workarounds. With them, the output matches the native formatter on every snapshot in
`../tests`; the one behavioural difference is described under
[ABI 14](#the-grammar-is-built-at-abi-14). Topiary 0.8.0 doesn't help: it needs the same
first three and its wasm code has more compile errors (checked October 2026).

### topiary-core 0.7.3 is patched

**What:** `topiary-core-wasm.patch` changes two lines; `make` downloads the crate from
crates.io into `target/vendor` and applies it, and `Cargo.toml` points `[patch.crates-io]`
at that copy.

**Why:** topiary-core's `wasm32` code path doesn't compile as published. It calls
`Node::language_name` and copies a `Range`, which the web-tree-sitter side of Topiary's
facade doesn't provide. Both only label error messages.

**Effect:** none on formatting. Parse errors have no language name attached.

**Remove when:** a Topiary release compiles for `wasm32-unknown-unknown`.

### web-tree-sitter is pinned to 0.21.0

**What:** the npm package that does the parsing at runtime; topiary-core calls into it on
wasm32.

**Why:** Topiary's binding (`topiary-web-tree-sitter-sys`) targets the pre-0.22 API, e.g.
`TreeCursor.currentNode()` as a method (a property from 0.22) and the global
`TreeSitter.init()` (named ES exports from 0.25). 0.21.0 is the last release it works with.

**Effect:**

- It's an old release line that gets no fixes.
- It can't load ABI 15 grammars, hence the next workaround.
- A host that also uses tree-sitter for highlighting with a newer web-tree-sitter can't
  share either with this formatter. It ships two of each (web-tree-sitter is about 250 KB,
  the IML grammar about 2.5 MB); they don't conflict.

**Remove when:** Topiary's binding is updated for web-tree-sitter >= 0.25.

### The grammar is built at ABI 14

**What:** `make` regenerates the parser with `tree-sitter generate --abi 14` in
`target/grammar-abi14`; the committed parser in `grammars/iml/src` stays at ABI 15.

**Why:** web-tree-sitter 0.21 can't load ABI 15 grammars.

**Effect:** ABI 14 has no `reserved` words, which the grammar uses to stop IML keywords
(`theorem`, `test`, `verify`, `lemma`, `instance`, ...) being used as identifiers. So the
wasm formatter accepts, and formats, some invalid IML that the native one rejects:

| Input                       | Native (ABI 15) | wasm (ABI 14) |
| --------------------------- | --------------- | ------------- |
| `let theorem = 1`           | parse error     | formatted     |
| `let x = test`              | parse error     | formatted     |
| `type t = { verify : int }` | parse error     | formatted     |
| `let x = r.lemma`           | parse error     | formatted     |

Valid IML parses identically: all 70 `.iml` files in this repo give the same trees with
both parsers, and keywords as attribute names (`[@@theorem]`) work. Formatting doesn't
change meaning, so the output is as invalid as the input and ImandraX still rejects it;
the wasm formatter just can't double as a check for this mistake. `test.mjs` checks these
cases, so it fails (as a reminder to update this section) once the leniency goes away.

**Remove when:** web-tree-sitter can be upgraded (previous workaround).

### tree-sitter-language is pinned to 0.1.7

**What:** `tree-sitter-language = "=0.1.7"` in `Cargo.toml`, though nothing here uses it
directly.

**Why:** topiary-core depends on native tree-sitter 0.26 even on wasm32. tree-sitter-language
supplies the libc stand-ins that tree-sitter's C code needs to compile for
`wasm32-unknown-unknown`, and from 0.1.8 it refuses to for tree-sitter 0.26 ("upgrade
tree-sitter to 0.27 or newer").

**Effect:** none at runtime. On wasm32 topiary-core never calls native tree-sitter, and the
linker drops all of its C code: the built module has no `ts_*` functions. It only has to
compile.

**Remove when:** Topiary depends on tree-sitter >= 0.27.

### Globals

Topiary's binding works through globals: `index.js` sets `TreeSitter` (and a stand-in
`Window` class when the host has none, as in Node and web workers), and `init` then sets
`Parser` and `Language`.
