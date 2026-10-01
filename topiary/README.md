# Topiary formatter for IML

An IML code formatter built on [Topiary](https://topiary.tweag.io/), the Tree-sitter-based
formatter from Tweag. It uses the IML grammar in this repo together with Topiary's official
OCaml formatting rules, adapted for IML.

Topiary mostly edits the whitespace between the nodes of the parse tree. Apart from a few
explicit query rules (e.g. adding or removing the optional leading `|` in `match`/`function`
cases), the source text of every token is copied through unchanged. So, unlike a formatter
that re-prints an AST, it won't drop parentheses, list brackets, string escapes or comments.

## Requirements

- **Topiary CLI 0.7.x** (tested with v0.7.3). Download a binary from the
  [releases page](https://github.com/tweag/topiary/releases), or `cargo install topiary-cli`.
  Set `TOPIARY=/path/to/topiary` if it's not on your `PATH`.
- **The compiled IML grammar** at `../grammars/iml/libtree-sitter-iml.{dylib,so}`.
  The macOS library is committed; on other platforms build it with
  `cd grammars/iml && gmake`.

## Usage

```bash
./format.sh path/to/file.iml ...   # format files in place
./format.sh < in.iml > out.iml     # stdin to stdout
```

`format.sh` can be run from any directory. Extra Topiary options go through `TOPIARY_ARGS`,
e.g. `TOPIARY_ARGS=-v ./format.sh file.iml`.

Topiary refuses to format input that doesn't parse, and it checks that formatting the result
again changes nothing (idempotence). In both cases it exits non-zero and leaves files unchanged.

To call Topiary directly instead, run it from this folder, because Topiary 0.7.x resolves the
relative grammar path in `languages.ncl` against the current directory:

```bash
cd topiary
TOPIARY_LANGUAGE_DIR=$PWD/queries topiary -C languages.ncl format --language iml < file.iml
```

### Comparing with the prettier-based formatter

`format-prettier.sh` runs the experimental prettier-based formatter from imandrax-vscode
(`imlformat/`, VS Code setting `imandrax.IMLFormatter`) with the same options as the
extension. It has the same interface as `format.sh`.

It expects the imandrax-vscode repo next to this one (`../../imandrax-vscode` from this folder), with `npm install` already run. 

Like the extension, its output has no trailing newline, so ignore that difference when comparing. 
Because it re-prints the AST, it can silently change what the code means.

## Core files

| File | Purpose |
|---|---|
| `languages.ncl` | Topiary configuration declaring the `iml` language and its grammar |
| `iml-extra.scm` | Hand-written formatting rules for IML-only syntax. **Edit this one.** |
| `queries/iml.scm` | The query Topiary loads. **Generated**: don't edit by hand |
| `update-queries.sh` | Regenerates `queries/iml.scm` |
| `format.sh` | Wrapper that finds the grammar for your platform and runs Topiary |
| `format-prettier.sh` | Runs the prettier-based formatter from imandrax-vscode, for comparison |
| `tests/` | Snapshot tests: `<name>.iml` inputs and `<name>.formatted.iml` expected outputs |
| `Makefile` | Runs the snapshot tests: `make test`, `make diff`, `make promote` |
| `LICENSE-topiary` | Topiary's MIT licence, which covers the OCaml rules in `queries/iml.scm` |

## How the query is built

`update-queries.sh` downloads Topiary's `ocaml.scm` at a pinned release tag, adapts it to
the IML grammar, and appends `iml-extra.scm`:

1. **Node-type renames.** The IML grammar is forked from a newer tree-sitter-ocaml than the
   one Topiary pins. `product_expression` is renamed to `tuple_expression`, and the rule for
   `typed_label` (which no longer exists) is removed. Every other node type the OCaml
   rules use exists in the IML grammar.
2. **IML statements** (`iml-extra.scm`): `axiom`, `theorem`, `lemma`, `verify`, `instance`,
   `eval`, `test` and `qcheck` get the same treatment as top-level `let`. That means a line
   break between items, a space after the keyword and before `=`, the body indented under `=`
   when the statement spans several lines, and attributes on their own line.
3. **Toplevel directives** (`#show foo`): keeps the space after the directive name. Without
   this rule Topiary prints `#showfoo`. That bug is in Topiary's own OCaml rules too.

## Testing

Expect-test is used. See `tests/` dir and relevant Make recipes.

## Known limitations

- **No line-width limit.** Topiary keeps the author's choice of single- vs multi-line layout
  instead of reflowing to a fixed width like ocamlformat. Long lines stay long, and oddly
  broken input stays oddly shaped.
- **Style is Topiary's OCaml style**, e.g. record fields as `id: int`, infix operators such as
  `@` at the end of the line, and a space added in `~on_fun: [%id …]`. Change these in the query.
- **Trailing comments after `;`, `in` or `->` move onto their own line** (see "Comments"
  above).
- **Rules can fall out of date.** The adapted query follows Topiary's pinned
  tree-sitter-ocaml, so grammar changes on either side may need the rename list updated.

## Licence

The OCaml rules in `queries/iml.scm` come from
[Topiary](https://github.com/tweag/topiary) and are used under its MIT licence
(Copyright (c) Tweag I/O Limited). The licence text is in `LICENSE-topiary`, and
`update-queries.sh` copies it into the header of the generated `queries/iml.scm`, as the
licence requires. Everything else in this folder is covered by this repository's
[licence](../LICENSE).
