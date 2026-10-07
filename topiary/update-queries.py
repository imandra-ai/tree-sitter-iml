#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Regenerate queries/iml.scm from Topiary's upstream OCaml query plus iml-extra.scm.

    queries/iml.scm = licence header + adapted upstream ocaml.scm + iml-extra.scm

Usage: ./update-queries.py [topiary-tag]   (default: v0.7.3)

Each adaptation names the exact upstream text it expects, and the script fails if that text is
missing, so an upstream change can't silently drop one. To add an adaptation, append to RENAMES
or PATCHES.
"""

import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path

DEFAULT_TAG = "v0.7.3"
HERE = Path(__file__).resolve().parent
OUT = HERE / "queries" / "iml.scm"


@dataclass
class Patch:
    why: str
    old: str  # exact upstream text, expected exactly once
    new: str


# Node-type renames
# =================
#
# The IML grammar is forked from a newer tree-sitter-ocaml than the one Topiary pins.

RENAMES = {
    "product_expression": "tuple_expression",
}


# Rule patches
# ============

PATCHES = [
    Patch(
        why="`typed_label` no longer exists in the newer tree-sitter-ocaml",
        old="""\
(typed_label
  ":" @append_spaced_softline
)
""",
        new="",
    ),
    # Upstream ends the let-binding indent after its last child (the trailing `.` anchor).
    # When an item attribute follows the body (`let f x = ... [@@measure ...]`), the attribute
    # is that last child and gets indented. Ending the indent after `body:` instead puts the
    # attribute back at the column of `let`, as for `theorem`.
    Patch(
        why="end the let-binding indent after the body, not after item attributes",
        old="""\
  "="
  (_
    ; any node that doesn't add its own indentation
    .
    [
      "fun" ; fun_expression
      "function" ; function_expression
      "[" ; list_expression
      "[|" ; array_expression
      "{" ; record_expression. Unfortunately this also captures quoted strings
      "(" ; parenthesized_expression. Unfortunately this also captures unit
    ]? @do_nothing
  ) @append_indent_end
  .
)
""",
        new="""\
  "="
  body: (_
    ; any node that doesn't add its own indentation
    .
    [
      "fun" ; fun_expression
      "function" ; function_expression
      "[" ; list_expression
      "[|" ; array_expression
      "{" ; record_expression. Unfortunately this also captures quoted strings
      "(" ; parenthesized_expression. Unfortunately this also captures unit
    ]? @do_nothing
  ) @append_indent_end
)
""",
    ),
    Patch(
        why="same as above, for the quoted-string and unit special case",
        old="""\
  "="
  [
    (quoted_string)
    (unit)
  ] @append_indent_end
  .
)
""",
        new="""\
  "="
  body: [
    (quoted_string)
    (unit)
  ] @append_indent_end
)
""",
    ),
    # Line break after `=`
    # ------------------
    #
    # Three upstream rules put a softline after `=`. A plain softline breaks when its parent
    # node spans several lines, and attributes count as part of the parent. So attributes on
    # the next line push a one-line body under `=`:
    #
    #   let f x = g x          becomes      let f x =
    #   [@@a]                                 g x
    #                                       [@@a]
    #
    # The three patches below make the break depend only on the right-hand side of `=`: it
    # breaks when the right-hand side spans several lines, or when the input already breaks
    # after `=`. The theorem/lemma/axiom rules in iml-extra.scm do the same.
    #
    # This one is the let-binding rule, for bodies that aren't covered by the other two. The
    # scope runs from `=` to the end of the body.
    Patch(
        why="break after a let-binding's `=` only when the body spans several lines",
        old="""\
(let_binding
  "=" @append_spaced_softline
  .
  [
    ; expressions
    (_
      .
      [
        "("
        "["
      ]
    )
    (list_expression)
    (record_expression)
    (array_expression)
    (function_expression)
    (fun_expression)
  ]* @do_nothing
)
""",
        new="""\
(let_binding
  "=" @append_spaced_scoped_softline
  .
  [
    ; expressions
    (_
      .
      [
        "("
        "["
      ]
    )
    (list_expression)
    (record_expression)
    (array_expression)
    (function_expression)
    (fun_expression)
  ]* @do_nothing
  (#scope_id! "let_body")
)
(let_binding
  "=" @append_begin_scope
  body: (_) @append_end_scope
  (#scope_id! "let_body")
)
""",
    ),
    # The general rule for `=` before an application, `if`, variable, tuple, variant, etc.
    # It has no parent node, so it applies to every `=`: `let`, `theorem`, `type t = A | B`,
    # record fields. Same fix: a scope from `=` to the end of the right-hand side, in the same
    # query (the scope begin sorts before the softline on `=`, so the softline is inside it).
    Patch(
        why="break after a general `=` only when the right-hand side spans several lines",
        old="""\
(
  "=" @append_spaced_softline
  .
  [
    (application_expression)
    (class_body_type)
    (if_expression)
    (function_type)
    (let_expression)
    (object_expression)
    (tuple_expression)
    (sequence_expression)
    (set_expression)
    (typed_expression)
    (unit)
    (value_path)
    (variant_declaration)
  ]
)
""",
        new="""\
(
  "=" @append_begin_scope @append_spaced_scoped_softline
  .
  [
    (application_expression)
    (class_body_type)
    (if_expression)
    (function_type)
    (let_expression)
    (object_expression)
    (tuple_expression)
    (sequence_expression)
    (set_expression)
    (typed_expression)
    (unit)
    (value_path)
    (variant_declaration)
  ] @append_end_scope
  (#scope_id! "equals_rhs")
)
""",
    ),
    # The "dangling list" rule for `=` (and `in`, `then`, `:`, ...) before a list, record,
    # array or parenthesized expression. Upstream wraps the softline in
    # `#single_line_scope_only! "dangling_list_like"`, so it only applies when that
    # list-like node fits on one line. A multi-line one stays attached to the token instead
    # (`let foo = {` + newline). Topiary can't nest a scoped softline inside that condition:
    # the condition resolves to the inner atom after scoped softlines are resolved, so the
    # inner one would be left unresolved and dropped.
    #
    # The `=` case is split out instead, with `@append_input_softline` (break only if the
    # input breaks after `=`). The condition already guarantees that the right-hand side is
    # on one line, so this is the same as the scoped version. The other tokens keep upstream's
    # rule unchanged.
    Patch(
        why="break after `=` before a one-line list or record only if the input does",
        old="""\
(_
  [
    (concat_operator)
    "in"
    "of"
    "then"
    "else"
    "private"
    "="
    "+="
    ":"
    "::"
    "<-"
    "*"
  ] @append_spaced_softline @append_indent_start
  .
  _? @do_nothing
  .
  (comment)*
  .
  (_
    .
    [
      "("
      "["
      "[|"
      "{"
    ]
    [
      ")"
      "]"
      "|]"
      "}"
    ] @prepend_indent_end
    .
  )
  .
  "="? @do_nothing ; Abort if we're in a let binding before the `=`
  (#single_line_scope_only! "dangling_list_like")
)
""",
        new="""\
(_
  [
    (concat_operator)
    "in"
    "of"
    "then"
    "else"
    "private"
    "+="
    ":"
    "::"
    "<-"
    "*"
  ] @append_spaced_softline @append_indent_start
  .
  _? @do_nothing
  .
  (comment)*
  .
  (_
    .
    [
      "("
      "["
      "[|"
      "{"
    ]
    [
      ")"
      "]"
      "|]"
      "}"
    ] @prepend_indent_end
    .
  )
  .
  "="? @do_nothing ; Abort if we're in a let binding before the `=`
  (#single_line_scope_only! "dangling_list_like")
)
; IML: the same rule for `=`, but breaking only where the input does (see update-queries.py)
(_
  "=" @append_input_softline @append_indent_start
  .
  _? @do_nothing
  .
  (comment)*
  .
  (_
    .
    [
      "("
      "["
      "[|"
      "{"
    ]
    [
      ")"
      "]"
      "|]"
      "}"
    ] @prepend_indent_end
    .
  )
  .
  "="? @do_nothing ; Abort if we're in a let binding before the `=`
  (#single_line_scope_only! "dangling_list_like")
)
""",
    ),
    # Upstream puts a softline before every item attribute, so in a multi-line item each
    # attribute gets its own line. iml-extra.scm lays them out as a group instead (see "Item
    # attributes" there).
    Patch(
        why="leave the line breaks before item attributes to iml-extra.scm",
        old="""\
  (else_clause)
  (item_attribute)
  "*"
""",
        new="""\
  (else_clause)
  "*"
""",
    ),
]


# Main
# ====


def fail(message: str) -> None:
    sys.exit(f"update-queries.py: {message}; check the upstream query")


def adapt(query: str) -> str:
    for old, new in RENAMES.items():
        if old not in query:
            fail(f"node type `{old}` not found")
        query = query.replace(old, new)
    for patch in PATCHES:
        count = query.count(patch.old)
        if count != 1:
            fail(f"expected 1 match, found {count}, for patch: {patch.why}")
        query = query.replace(patch.old, patch.new)
    return query


def header(tag: str, url: str) -> str:
    licence = (HERE / "LICENSE-topiary").read_text().splitlines()
    lines = [
        f"GENERATED by update-queries.py from Topiary {tag}:",
        f"  {url}",
        "Do not edit by hand: change iml-extra.scm or the adaptations in update-queries.py,",
        "then rerun.",
        "",
        "The OCaml rules below are from Topiary and are used under its licence",
        "(also in LICENSE-topiary):",
        "",
        *licence,
    ]
    return "".join(f"; {line}".rstrip() + "\n" for line in lines) + "\n"


def main() -> None:
    tag = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TAG
    url = f"https://raw.githubusercontent.com/tweag/topiary/{tag}/topiary-queries/queries/ocaml.scm"
    with urllib.request.urlopen(url) as response:
        upstream = response.read().decode()
    # Build everything before writing, so a failure leaves the existing query untouched.
    query = (
        header(tag, url)
        + adapt(upstream).rstrip("\n")
        + "\n"
        + (HERE / "iml-extra.scm").read_text()
    )
    OUT.write_text(query)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
