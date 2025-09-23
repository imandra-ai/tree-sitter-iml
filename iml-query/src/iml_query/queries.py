"""Query source strings and definitions for IML tree-sitter queries."""

VERIFY_QUERY_SRC = r"""
(verify_statement) @verify
"""

INSTANCE_QUERY_SRC = r"""
(instance_statement) @instance
"""

AXIOM_QUERY_SRC = r"""
(axiom_definition) @axiom
"""

THEOREM_QUERY_SRC = r"""
(theorem_definition) @theorem
"""

LEMMA_QUERY_SRC = r"""
(lemma_definition) @lemma
"""

DECOMP_QUERY_SRC = r"""
(value_definition
    (let_binding
        (value_name) @decomposed_func_name
        (item_attribute
            (attribute_id) @_decomp_id
            (attribute_payload) @decomp_payload
            (#eq? @_decomp_id "decomp")
        ) @decomp_attr
    )
)
"""

EVAL_QUERY_SRC = r"""
(eval_statement) @eval
"""

OPAQUE_QUERY_SRC = r"""
(value_definition
    (let_binding
        (value_name) @func_name
        (item_attribute
            (attribute_id) @attribute_id
            (#eq? @attribute_id "opaque")
        ) @item_attr
    )
) @full_def
"""

# TODO:
# (path import with explicit module name)
# [@@@import Mod_name, "path/to/file.iml"]
# (same, with explicit extraction name)
# [@@@import Mod_name, "path/to/file.iml", Mod_name2]
# (path import as module `File`)
# [@@@import "path/to/file.iml"]
# (import from ocamlfind library)
# [@@@import Mod_name, "findlib:foo.bar"]
# (same, with explicit extraction name)
# [@@@import Mod_name, "findlib:foo.bar", Mod_name2]
# (import from dune library)
# [@@@import Mod_name, "dune:foo.bar"]
# (same, with explicit extraction name)
# [@@@import Mod_name, "dune:foo.bar", Mod_name2]

GENERAL_IMPORT_QUERY_SRC = r"""
(floating_attribute
    "[@@@"
    (attribute_id) @attribute_id
    (#eq? @attribute_id "import")
) @import
"""

IMPORT_1_QUERY_SRC = r"""
(floating_attribute
    "[@@@"
    (attribute_id) @attribute_id
    (#eq? @attribute_id "import")
    (attribute_payload
        (expression_item
            (tuple_expression
                (constructor_path
                    (constructor_name) @import_name
                )
                (string
                    (string_content) @import_path
                )
            )
        )
    )
) @import
"""

IMPORT_3_QUERY_SRC = r"""
(floating_attribute
    "[@@@"
    (attribute_id) @attribute_id
    (#eq? @attribute_id "import")
    (attribute_payload
        (expression_item
            (string
                (string_content) @import_path
            )
        )
    )
) @import
"""

VALUE_DEFINITION_QUERY_SRC = r"""
(value_definition
    (let_binding
        (value_name) @function_name
    )
) @function_definition
"""
