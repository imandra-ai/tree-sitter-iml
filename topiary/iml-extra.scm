
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

; Floating attributes (`[@@@import M, "m.iml"]`) sit on their own line. Topiary's OCaml
; rules add no line break before or after them, so they would be joined onto the line of
; the neighbouring item. As above, the next item is listed explicitly so a trailing
; comment stays put.
(
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
    (item_extension)
    (quoted_item_extension)
    (toplevel_directive)
  ] @append_hardline
  .
  (floating_attribute)
)
(compilation_unit
  (floating_attribute) @append_hardline
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
    (toplevel_directive)
  ]
)
(structure
  (floating_attribute) @append_hardline
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
  ]
)

; Opting out of formatting
; ========================

; `[@@imlformat "disable"]` on an item keeps that item exactly as written. For `let`,
; `type` and `module` the attribute belongs to one binding, but the whole item is kept.
(
  [
    (value_definition
      (let_binding
        (item_attribute (attribute_id) @_id (attribute_payload) @_payload)))
    (type_definition
      (type_binding
        (item_attribute (attribute_id) @_id (attribute_payload) @_payload)))
    (module_definition
      (module_binding
        (item_attribute (attribute_id) @_id (attribute_payload) @_payload)))
    (external
      (item_attribute (attribute_id) @_id (attribute_payload) @_payload))
    (exception_definition
      (item_attribute (attribute_id) @_id (attribute_payload) @_payload))
    (module_type_definition
      (item_attribute (attribute_id) @_id (attribute_payload) @_payload))
    (open_module
      (item_attribute (attribute_id) @_id (attribute_payload) @_payload))
    (include_module
      (item_attribute (attribute_id) @_id (attribute_payload) @_payload))
    (axiom_definition
      (item_attribute (attribute_id) @_id (attribute_payload) @_payload))
    (theorem_definition
      (item_attribute (attribute_id) @_id (attribute_payload) @_payload))
    (lemma_definition
      (item_attribute (attribute_id) @_id (attribute_payload) @_payload))
    (verify_statement
      (item_attribute (attribute_id) @_id (attribute_payload) @_payload))
    (instance_statement
      (item_attribute (attribute_id) @_id (attribute_payload) @_payload))
    (eval_statement
      (item_attribute (attribute_id) @_id (attribute_payload) @_payload))
    (test_statement
      (item_attribute (attribute_id) @_id (attribute_payload) @_payload))
    (qcheck_statement
      (item_attribute (attribute_id) @_id (attribute_payload) @_payload))
  ] @leaf
  (#eq? @_id "imlformat")
  (#eq? @_payload "\"disable\"")
)

; `[@@@imlformat "disable"]` as the first item of a file (only comments may come before
; it) keeps the whole file exactly as written.
(compilation_unit
  .
  (comment)*
  .
  (floating_attribute (attribute_id) @_id (attribute_payload) @_payload)
  (#eq? @_id "imlformat")
  (#eq? @_payload "\"disable\"")
) @leaf
