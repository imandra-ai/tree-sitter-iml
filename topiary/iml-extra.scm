
; IML-specific top-level statements
; =================================

[
  (axiom_definition)
  (theorem_definition)
  (lemma_definition)
  (verify_statement)
  (instance_statement)
  (eval_statement)
  (test_statement)
  (qcheck_statement)
] @allow_blank_line_before

; Each IML statement sits on its own line, separated from its neighbours.
; The neighbours are listed explicitly rather than matched with `(_)`, which would also
; match a trailing comment and push it onto its own line.
(compilation_unit
  [
    (value_definition)
    (external)
    (type_definition)
    (exception_definition)
    (module_definition)
    (module_type_definition)
    (open_module)
    (include_module)
    (class_definition)
    (class_type_definition)
    (floating_attribute)
    (item_extension)
    (quoted_item_extension)
    (axiom_definition)
    (theorem_definition)
    (lemma_definition)
    (verify_statement)
    (instance_statement)
    (eval_statement)
    (test_statement)
    (qcheck_statement)
    (toplevel_directive)
  ] @append_hardline
  .
  [
    (axiom_definition)
    (theorem_definition)
    (lemma_definition)
    (verify_statement)
    (instance_statement)
    (eval_statement)
    (test_statement)
    (qcheck_statement)
  ]
)
(compilation_unit
  [
    (axiom_definition)
    (theorem_definition)
    (lemma_definition)
    (verify_statement)
    (instance_statement)
    (eval_statement)
    (test_statement)
    (qcheck_statement)
  ] @append_hardline
  .
  [
    (value_definition)
    (external)
    (type_definition)
    (exception_definition)
    (module_definition)
    (module_type_definition)
    (open_module)
    (include_module)
    (class_definition)
    (class_type_definition)
    (floating_attribute)
    (item_extension)
    (quoted_item_extension)
    (axiom_definition)
    (theorem_definition)
    (lemma_definition)
    (verify_statement)
    (instance_statement)
    (eval_statement)
    (test_statement)
    (qcheck_statement)
    (toplevel_directive)
  ]
)

[
  "axiom"
  "theorem"
  "lemma"
  "verify"
  "instance"
  "eval"
  "test"
  "qcheck"
] @append_space

; `theorem name params = body`: like let_binding, break after `=` and indent
; the body when the statement spans several lines. The body is matched by its field
; name, so a comment between `=` and the body doesn't end the indentation early.
(axiom_definition
  "=" @prepend_space @append_spaced_softline @append_indent_start
  body: (_) @append_indent_end
)
(theorem_definition
  "=" @prepend_space @append_spaced_softline @append_indent_start
  statement: (_) @append_indent_end
)
(lemma_definition
  "=" @prepend_space @append_spaced_softline @append_indent_start
  statement: (_) @append_indent_end
)

; Attributes go on their own line in multi-line statements.
(axiom_definition
  (item_attribute) @prepend_spaced_softline
)
(theorem_definition
  (item_attribute) @prepend_spaced_softline
)
(lemma_definition
  (item_attribute) @prepend_spaced_softline
)
(verify_statement
  (item_attribute) @prepend_spaced_softline
)
(instance_statement
  (item_attribute) @prepend_spaced_softline
)
(eval_statement
  (item_attribute) @prepend_spaced_softline
)
(test_statement
  (item_attribute) @prepend_spaced_softline
)
(qcheck_statement
  (item_attribute) @prepend_spaced_softline
)

; Toplevel directives (`#show foo`): keep the space after the directive name and
; put each one on its own line. Also missing from Topiary's own OCaml queries.
(toplevel_directive
  (directive) @append_space
)
(compilation_unit
  (toplevel_directive) @append_hardline
  .
  [
    (value_definition)
    (external)
    (type_definition)
    (exception_definition)
    (module_definition)
    (module_type_definition)
    (open_module)
    (include_module)
    (class_definition)
    (class_type_definition)
    (floating_attribute)
    (item_extension)
    (quoted_item_extension)
    (axiom_definition)
    (theorem_definition)
    (lemma_definition)
    (verify_statement)
    (instance_statement)
    (eval_statement)
    (test_statement)
    (qcheck_statement)
    (toplevel_directive)
  ]
)
