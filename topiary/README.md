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
extension. It has the same interface as `format.sh`:

```bash
./format-prettier.sh path/to/file.iml ...   # format files in place
./format-prettier.sh < in.iml > out.iml     # stdin to stdout

diff <(./format.sh < in.iml) <(./format-prettier.sh < in.iml)
```

It expects the imandrax-vscode repo next to this one (`../../imandrax-vscode` from this
folder), with `npm install` already run. Set `IMANDRAX_VSCODE` to use another checkout. The
first run bundles the formatter with esbuild into the system temp directory (about 2 s).
Later runs reuse that bundle until the formatter's sources change. Neither repo is
modified.

Like the extension, its output has no trailing newline, so ignore that difference when
comparing. Because it re-prints the AST, it can silently change what the code means (see
"Example: why not the prettier-based formatter"), so use it on copies.

## Files

| File | Purpose |
|---|---|
| `languages.ncl` | Topiary configuration declaring the `iml` language and its grammar |
| `iml-extra.scm` | Hand-written formatting rules for IML-only syntax. **Edit this one.** |
| `queries/iml.scm` | The query Topiary loads. **Generated**: don't edit by hand |
| `update-queries.sh` | Regenerates `queries/iml.scm` |
| `format.sh` | Wrapper that finds the grammar for your platform and runs Topiary |
| `format-prettier.sh` | Runs the prettier-based formatter from imandrax-vscode, for comparison |
| `examples/pair_list.iml` | Example the prettier-based IML formatter breaks (see below) |
| `tests/` | Snapshot tests: `<name>.iml` inputs and `<name>.formatted.iml` expected outputs (see "Testing") |
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

To move to a newer Topiary release:

```bash
./update-queries.sh v0.7.4
```

The script stops if the upstream rules no longer contain the `typed_label` rule it removes.
In that case, check whether the upstream file changed the node types listed above.
Topiary also refuses to load a query that names a node type the grammar lacks, and its error
gives the line number.

When you add a statement keyword to `grammars/iml/grammar.js`, add its node to the lists in
`iml-extra.scm` and rerun `./update-queries.sh`. Otherwise Topiary strips the whitespace
around it, e.g. `let a = 1theoremt x = …`.

## Testing

### Snapshot tests

`tests/` is one flat folder of test pairs: `<name>.iml` is an IML snippet and
`<name>.formatted.iml` is the expected Topiary output. The name prefix gives the category
(`syntax_`, `iml_`, `comments_`, `strings_`). [`tests/README.md`](tests/README.md) says
what each test checks.

Run them from this folder with the Makefile:

```bash
make test     # format each <name>.iml to <name>.out.iml and compare with <name>.formatted.iml
make diff     # show the differences as unified diffs (expected -> actual)
make promote  # accept the new output: copy each differing .out.iml over its .formatted.iml
make clean    # remove the generated .out.iml files
```

`make test` never changes the expected files. It reformats every input from scratch, prints
`FAIL` for a test whose output differs and `ERROR` for one Topiary refused to format, and
exits non-zero if any test didn't pass. Limit any target to some tests with `T`, e.g.
`make test T=comments_doc` or `make diff T='iml_% strings_%'`.

Formatting also runs Topiary's idempotence check, so a test fails if formatting the output
again would change it. After an intended style change, review `make diff` and accept the
new output with `make promote`. To add a test, write `tests/<name>.iml`, run
`make promote T=<name>` to create its `.formatted.iml`, and check that file by hand.

The expected outputs were checked once, with the methods described below, to make sure
the formatted code means the same as the input. When adding a test, check its expected
output the same way before accepting it.

### Corpus results

Results from 2026-10-01, Topiary v0.7.3:

- Every `.iml` file under `../iml_examples/` (40 files), plus two IML files from the
  imandrax-vscode formatter tests (including a 1,287-line one), was formatted and checked:
  - the ImandraX IML parser gives the same AST for input and output (ignoring locations),
  - all `(* … *)` comments are still present,
  - formatting the output again changes nothing.
- All 42 files pass.

### Comments

Comments are hard for formatters that re-print an AST, because the OCaml parser drops
them. In tree-sitter they are ordinary nodes in the tree, and Topiary copies their text
through, so it never has to reconstruct them. The `comments_*` and `strings_*` tests
put comments in awkward places: nested `(* (* *) *)`; `*)`
inside a string within a comment; inside parentheses, tuples, lists, records, types,
patterns, guards and attributes; between a keyword and a name; doc comments; and ASCII
art. These cases, plus the 42 files above, were checked for:

- the same sequence of tokens and comments, so nothing is lost, duplicated, reordered or
  moved across a token;
- comment text unchanged, or only shifted along with the surrounding code;
- each comment still at the end of a code line, or still on its own line.

Results:

- No comment is lost, duplicated or moved past any code.
- Multi-line comments are re-indented as a block, so their internal layout (ASCII art,
  commented-out code) is kept.
- **One known change:** a comment at the end of a line that ends with `;`, `in` or `->`
  moves onto its own line, e.g. `print x; (* c *)` becomes `print x;` then `(* c *)`. This
  comes from Topiary's own OCaml rules, which do the same to `.ml` files. Meaning is
  unaffected.

**Strings inside comments.** OCaml reads string literals inside comments, so a `*)` inside
a `"…"` in a comment doesn't close the comment. The tree-sitter grammar matches the real IML
parser on every valid case tested: an escaped `\"` in a commented string; `*)` inside a
commented string, including one spanning lines; `{id| … |id}` quoted strings; a `'"'` char
literal; an apostrophe as in `it's`; a doc comment containing a string; `(*` inside a normal
string; and `(* " *) let hidden = 1 (* " *)`, where `let hidden` is inside the comment for
both parsers. Topiary formats all of these correctly.

The one disagreement is an **unbalanced `"` in a comment**, e.g. `(* unbalanced " quote *)`.
The real parser rejects the file (unterminated string). Tree-sitter reports no error and
treats everything from there to the end of the file as one comment. So Topiary doesn't
refuse: it formats the code before the comment and leaves the rest unchanged. Nothing is
corrupted, but the invalid file goes unreported.

Two bugs in `iml-extra.scm` found by these tests are fixed. A comment between `=` and a
theorem body ended the body's indentation early. A comment after an IML statement was
pushed onto its own line.

A quick self-check after changing the rules:

```bash
for f in ../iml_examples/*/*.iml; do ./format.sh < "$f" > /dev/null || echo "FAILED: $f"; done
```

This catches query errors, parse failures and idempotence failures, but not changes in
meaning. To check meaning, compare the parse trees of the input and output without
positions. In testing, `tree-sitter parse` printed nothing when two copies ran at once (as
in `diff <(…) <(…)`) or when its output went straight to a file. So run the two parses one
after the other and pipe through `cat`:

```bash
tsp() { tree-sitter parse -p ../grammars/iml --no-ranges "$1" 2>/dev/null | cat; }
./format.sh < in.iml > out.iml
tsp in.iml > in.tree; tsp out.iml > out.tree
[ -s in.tree ] && cmp in.tree out.tree && echo "same tree"
```

Run this from this folder. Comments appear as `(comment)` nodes in the tree, so dropping
one also shows up as a difference.

## Example: why not the prettier-based formatter

[`examples/pair_list.iml`](examples/pair_list.iml) is ordinary IML. The experimental
prettier-based formatter in imandrax-vscode (`imlformat/`, setting
`imandrax.IMLFormatter`) re-prints the AST and gets this wrong:

```ocaml
type pair_list = 'a * 'a list

let swap_all (l : int pair_list) : int pair_list =
  List.map (fun (a, b) -> b, a) l

let firsts (l : int pair_list) : int list =
  match l with [a, _b, _] -> a::b | _ -> []

let push (x : int) (y : int) (l : int pair_list) : int pair_list = x, y::l

theorem push_len x y l = List.length (push x y l) = List.length l + 1
```

- `type 'a pair_list = ('a * 'a) list` loses its type parameter and its parentheses, and
  now means "a pair whose second half is a list". `'a` is unbound.
- `[(a, _); (b, _)]` (two pairs) becomes `[a, _b, _]` (one triple). `_` and `b` merge
  into a new variable `_b`, and `[a; b]` becomes `a::b`.
- `(x, y) :: l` becomes `x, y::l`, i.e. the tuple `(x, y :: l)`.
- `(b, a)` → `b, a` is harmless only because the tuple is the whole function body.

The output still parses, so that formatter reports no error. Topiary leaves this file
unchanged:

```bash
./format.sh < examples/pair_list.iml | diff examples/pair_list.iml - && echo unchanged
```

The underlying causes in `imlformat/iml-prettier.ts` (as of imandrax-vscode `7c21cee`):
tuples, field access and single-argument type constructors never add parentheses; list
expressions are never printed as `[…]`; list patterns are joined without `;`; type
parameters are not printed; strings are not re-escaped. Topiary can't make any of these
mistakes, because it never re-prints tokens.

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
