# tree-sitter-iml

Tree-sitter grammar for **IML** (Imandra Modeling Language). Forked from
[tree-sitter-ocaml](https://github.com/tree-sitter/tree-sitter-ocaml) and extended
with IML-specific constructs. Packaged as a Python distribution (`tree-sitter-iml`)
and as C/Rust/Go/Swift bindings.

## Layout

- `grammars/iml/` — **the IML grammar.** This is what you edit.
  - `grammar.js` — the grammar source (the only hand-written file).
  - `src/{grammar.json,node-types.json,parser.c}` — **generated** artifacts, committed to the repo. Regenerate them; don't hand-edit.
  - `libtree-sitter-iml.{a,dylib}` — **built** library artifacts, also committed.
- `grammars/{ocaml,interface,type}/` — upstream tree-sitter-ocaml grammars, kept for comparison. Usually leave these alone.
- `queries/highlights.scm` — syntax-highlighting query (shared, at repo root).
- `iml_examples/` — example `.iml` files grouped by feature, each with committed `.tree` snapshots (see below).
- `scripts/gen_tree.py` — dev tool to render an `.iml` file's parse tree to a `.tree` file.

IML-specific keywords live in `grammar.js`: `axiom`, `theorem`, `lemma`,
`verify`, `instance`, `eval`, `test`, `qcheck`. Each has a corresponding
`*_statement`/`*_definition` rule and an entry in `_structure_item`.

## Workflow: adding a keyword / changing the grammar

This is the end-to-end path (the `test` and `qcheck` keywords were added this way):

1. **Edit `grammars/iml/grammar.js`.** For a new top-level statement keyword you
   need three coordinated edits:
   - add the literal to the `reserved.global` list,
   - add the rule node (e.g. `$.test_statement`) to the `_structure_item` choice,
   - define the rule itself (e.g. `test_statement: $ => seq('test', ...)`).
2. **Regenerate the parser** (produces `src/grammar.json`, `src/node-types.json`, `src/parser.c`):
   ```bash
   cd grammars/iml && npx tree-sitter generate
   ```
3. **Rebuild the library** (`.a`/`.dylib`):
   ```bash
   cd grammars/iml && gmake     # GNU make required (see gotcha below)
   ```
4. **Update `queries/highlights.scm`** if the change adds user-visible tokens
   (e.g. add the keyword to the IML-specific keywords group).
5. **Add an example + snapshots** under `iml_examples/<feature>/` (see below).

Verify a parse quickly without installing anything:
```bash
cd grammars/iml && printf 'test (fun x -> x = x)\n' | npx tree-sitter parse /dev/stdin
```

## Examples and `.tree` snapshots

Each example feature dir (e.g. `iml_examples/qcheck/`, `iml_examples/test/`)
contains `basic.iml` plus two committed parse-tree snapshots:

- `basic.iml.tree` — parsed with the **IML** grammar.
- `basic.ocaml.tree` — parsed with the upstream **OCaml** grammar, for comparison
  (OCaml doesn't know IML keywords, so e.g. `test foo` parses as a function
  application — that contrast is the point of keeping both).

Generate them with `scripts/gen_tree.py`. It depends on the editable
`tree-sitter-iml` package, so `uv run` rebuilds the parser automatically — run
this *after* regenerating in step 2:
```bash
uv run scripts/gen_tree.py iml_examples/test/basic.iml          # -> basic.iml.tree
uv run scripts/gen_tree.py --ocaml iml_examples/test/basic.iml  # -> basic.ocaml.tree
```

## Make targets (from repo root)

`make help` lists them. The IML ones:
- `make generate-iml` — regenerate the IML parser.
- `make build-iml` — build the IML library.
- `make clean-iml` — clean IML build artifacts.
- `make build-python` / `make publish-python-{testpypi,pypi}` — package & publish.

## Gotchas

- **Use GNU make (`gmake`) for the IML grammar build.** The shared
  `common/common.mak` uses GNU-make `$(shell ...)` syntax that Apple's stock
  `/usr/bin/make` (BSD make) chokes on (`unterminated call to function shell`).
- The build's final pkg-config step (`tree-sitter-iml.pc`) errors looking for a
  missing `../../bindings/c/tree-sitter-iml.pc.in`. This is **pre-existing and
  harmless** — the `.a`/`.dylib` are produced before it fails.
- `src/parser.c` is huge (~hundreds of thousands of lines) and regenerated
  wholesale; expect a large diff on every grammar change. That's normal.
- `queries/highlights.scm` did not historically include the IML keywords; they
  were added as a dedicated "IML-specific keywords" group.

## Tooling conventions

- Python: managed with `uv`. Prefix Python commands with `uv run`. Lint with
  `uv run ruff check . --fix`, format with `uv run ruff format .`.
- `tree-sitter` CLI is a dev dependency; invoke via `npx tree-sitter`.
