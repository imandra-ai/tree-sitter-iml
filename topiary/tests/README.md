# Formatter snapshot tests

Each test is a pair: `<name>.iml` is the input and `<name>.formatted.iml` is the expected
Topiary output. Run them with `make test` from the parent folder (see the Makefile there).

The prefix gives the category:

| Prefix | Covers |
|---|---|
| `syntax_` | Plain OCaml syntax: types, expressions, lists, modules, literals |
| `iml_` | IML statements (`theorem`, `verify`, …) and toplevel directives |
| `comments_` | Comment placement: no comment is lost, duplicated or moved past code |
| `strings_` | Lexically tricky comments: nesting, and strings inside comments (OCaml reads string literals inside comments, so a `*)` inside a `"…"` in a comment doesn't end the comment) |

| Test | What it checks |
|---|---|
| `syntax_g_resolved` | `::` keeps its spaces, `Real.( ... )` is tidied. |
| `syntax_types` | Variants, records, and a parameterised type keep `'a` and the parentheses in `(int * real) list`. |
| `syntax_expressions` | Expressions: record update, `function`, `as` patterns, pipelines, negation, list literals, labelled and optional arguments, nested `let ... in`. |
| `syntax_list_literals` | List literals in expressions and patterns keep their brackets and `;`. |
| `syntax_modules_literals` | Modules, `open`, and literals: string escapes, chars, floats, nested tuples. |
| `syntax_pair_list` | Snippet that the prettier-based formatter breaks (see `../examples/pair_list.iml`). Topiary leaves it unchanged. |
| `iml_statements` | All IML statement kinds, with attributes, keep their spacing and line breaks. |
| `iml_adjacent_lines` | Statements on adjacent lines stay on their own lines; Topiary doesn't glue them together or insert blank lines between them. |
| `iml_multiline_theorem` | A multi-line theorem gets its body indented under `=`. |
| `iml_directives` | Toplevel directives keep the space after the directive name (Topiary's own OCaml rules print `#showfoo`). |
| `iml_floating_attributes` | Floating attributes (`[@@@import ...]`) stay on their own line, at the top level and in a `struct`; a trailing comment stays on the same line. |
| `iml_disable_item` | `[@@imlformat "disable"]` keeps that item as written (for `let ... and`, the whole definition); the other items are still formatted. |
| `iml_disable_file` | `[@@@imlformat "disable"]` as the first item (after comments) keeps the whole file as written. |
| `iml_disable_file_not_first` | `[@@@imlformat "disable"]` anywhere else has no effect. |
| `comments_let_and_match` | Comments before, inside and after a `let`, and on match cases. |
| `comments_expressions` | Comments between tokens of expressions, inside parentheses, tuples, lists, records and functions. Known change from Topiary's OCaml rules: the comment after `print x;` moves onto its own line. |
| `comments_patterns` | Comments in match cases, guards and patterns. |
| `comments_types` | Comments in variant, record, arrow and tuple types. |
| `comments_doc` | Doc comments stay attached to the item they document. |
| `comments_multiline` | Multi-line comments keep their internal layout (ASCII art, indented continuation lines). Extra blank lines are reduced to one. |
| `comments_iml_statements` | Comments inside and after IML statements, including inside an attribute. |
| `comments_theorem_body` | A comment between `=` and a theorem body doesn't end the body's indentation early. |
| `comments_only` | A file with only comments. |
| `strings_nested_and_banners` | Nested comments, banners, and `(*` inside strings and quoted strings. |
| `strings_escaped_quote` | Escaped quote inside a commented string. |
| `strings_escaped_quote_only` | A commented string that is just an escaped quote. |
| `strings_closer_multiline` | `*)` inside a commented string that spans lines. |
| `strings_hidden_code` | Code inside a commented string is part of the comment: `let hidden` is not formatted. |
| `strings_quoted_string` | `*)` inside a quoted string `{id\| ... \|id}` in a comment. |
| `strings_apostrophe` | An apostrophe, as in `it's`, doesn't start a char literal. |
| `strings_char_quote` | A `'"'` char literal doesn't start a string. |
| `strings_doc_comment` | Doc comment containing a string with `*)`. |
| `strings_opener_in_string` | `(*` inside a normal string doesn't start a comment. |
| `strings_unbalanced_quote` | Known limitation: an unbalanced `"` in a comment. The real IML parser rejects this file; tree-sitter instead treats everything up to the end of the file as one comment, so the code after it is left unformatted (note the double spaces in `let b`). |

Formatting also runs Topiary's idempotence check: if formatting the output again would
change it, Topiary exits with an error and the test reports `ERROR`.
