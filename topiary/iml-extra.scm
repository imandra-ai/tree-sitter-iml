
; IML-specific top-level statements
; =================================

[
  (axiom_definition)
  (theorem_definition)
  (lemma_definition)
  (rule_spec_definition)
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
    (rule_spec_definition)
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
    (rule_spec_definition)
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
    (rule_spec_definition)
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
    (rule_spec_definition)
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
  "rule_spec"
  "verify"
  "instance"
  "eval"
  "test"
  "qcheck"
] @append_space

; `theorem name params = body`: like let_binding, indent the body under `=`. The body is
; matched by its field name, so a comment between `=` and the body doesn't end the
; indentation early.
(axiom_definition
  "=" @prepend_space @append_indent_start
  body: (_) @append_indent_end
)
(theorem_definition
  "=" @prepend_space @append_indent_start
  statement: (_) @append_indent_end
)
(lemma_definition
  "=" @prepend_space @append_indent_start
  statement: (_) @append_indent_end
)
(rule_spec_definition
  "=" @prepend_space @append_indent_start
  statement: (_) @append_indent_end
)

; Break after `=` only when the body itself spans several lines: the scope runs from `=`
; to the end of the body, so attributes on the next line don't move the body. (A plain
; softline would follow the whole statement, attributes included.) The softline needs its
; own query: with the indent captures above in the same query, Topiary fails with "Trying
; to close an unopened indentation block".
(axiom_definition
  "=" @append_begin_scope
  body: (_) @prepend_spaced_scoped_softline @append_end_scope
  (#scope_id! "axiom_body")
)
(theorem_definition
  "=" @append_begin_scope
  statement: (_) @prepend_spaced_scoped_softline @append_end_scope
  (#scope_id! "theorem_body")
)
(lemma_definition
  "=" @append_begin_scope
  statement: (_) @prepend_spaced_scoped_softline @append_end_scope
  (#scope_id! "lemma_body")
)
(rule_spec_definition
  "=" @append_begin_scope
  statement: (_) @prepend_spaced_scoped_softline @append_end_scope
  (#scope_id! "rule_spec_body")
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
    (rule_spec_definition)
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
    (rule_spec_definition)
    (verify_statement)
    (instance_statement)
    (eval_statement)
    (test_statement)
    (qcheck_statement)
  ]
)

; Labelled arguments and parameters
; =================================
;
; No space after the label's colon: `f ~x:1 ?y:v`, `let f ~x:a = ...`, as ocamlformat prints
; them. Topiary's OCaml style is `~x: 1`. The colon of a typed parameter, `~(x : int)`,
; follows a pattern rather than a label_name, so it keeps its spaces.
(labeled_argument
  (label_name)
  .
  ":" @append_antispace
)
(parameter
  (label_name)
  .
  ":" @append_antispace
)

; Item attributes
; ===============
;
; Like ocamlformat, the attributes after an item (`[@@by auto] [@@rw]`) are laid out as a
; group: they start on a new line when the item spans several lines, and then either all
; share that line or each gets its own. Topiary can't measure width, so "all share a line"
; means they were written on one line. update-queries.py removes `item_attribute` from
; Topiary's rule that puts a softline before every attribute.
;
; The first attribute is the one after a node that is neither an attribute nor a comment.
; Topiary only accepts its own capture names, so that node is captured with
; `@prepend_space` (harmless, it always follows a space) to test it with `#match?`.
(_
  (_) @prepend_space
  .
  (comment)*
  .
  (item_attribute) @prepend_spaced_softline @prepend_begin_scope
  (#match? @prepend_space "^([^\\[(]|\\[[^@]|\\[@[^@]|\\([^*])")
  (#scope_id! "item_attributes")
)
; The predicate sits outside the node pattern: inside it, the trailing `.` anchor is
; ignored and the scope would end after every attribute.
(
  (_
    (item_attribute) @append_end_scope
    .
  )
  (#scope_id! "item_attributes")
)
(_
  (item_attribute)
  .
  (comment)*
  .
  (item_attribute) @prepend_spaced_scoped_softline
  (#scope_id! "item_attributes")
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
    (rule_spec_definition
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
