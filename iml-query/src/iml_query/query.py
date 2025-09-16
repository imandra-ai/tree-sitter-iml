from typing import Any, cast

import structlog
from tree_sitter import Node, Query, QueryCursor

from iml_query.tree_sitter_utils import get_language, get_parser

logger = structlog.get_logger(__name__)

iml_language = get_language(ocaml=False)


def mk_query(query_src: str) -> Query:
    """Create a Tree-sitter query from the given source."""
    return Query(iml_language, query_src)


def run_query(
    query: Query,
    code: str | bytes | None = None,
    node: Node | None = None,
) -> list[tuple[int, dict[str, list[Node]]]]:
    """Run a Tree-sitter query on the given code.

    Return:
        A list of tuples where the first element is the pattern index and
        the second element is a dictionary that maps capture names to nodes.

    """
    if code is None == node is None:
        raise ValueError('Exactly one of code or node must be provided')

    if code is not None:
        if isinstance(code, str):
            code = bytes(code, 'utf8')

        parser = get_parser(ocaml=False)
        tree = parser.parse(code)

        node = tree.root_node

    node = cast(Node, node)

    cursor = QueryCursor(query=query)
    return cursor.matches(node)


def group_captures(captures: dict[str, list[Node]]) -> dict[str, list[Node]]:
    """Group captures by their names."""
    return {name: nodes for name, nodes in captures.items() if name}


# =====


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
        (value_name) @func_name
        (item_attribute
            (attribute_id) @attribute_id
            (#eq? @attribute_id "decomp")
            (attribute_payload) @attribute_payload
        ) @item_attr
    )
) @decomposed_func
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
# [@@@import Mod_name, "path/to/file.iml"] (path import with explicit module name)
# [@@@import Mod_name, "path/to/file.iml", Mod_name2] (same, with explicit extraction name)
# [@@@import "path/to/file.iml"] (path import as module `File`)
# [@@@import Mod_name, "findlib:foo.bar"] (import from ocamlfind library)
# [@@@import Mod_name, "findlib:foo.bar", Mod_name2] (same, with explicit extraction name)
# [@@@import Mod_name, "dune:foo.bar"] (import from dune library)
# [@@@import Mod_name, "dune:foo.bar", Mod_name2] (same, with explicit extraction name)

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

verify_query = mk_query(VERIFY_QUERY_SRC)
instance_query = mk_query(INSTANCE_QUERY_SRC)
axiom_query = mk_query(AXIOM_QUERY_SRC)
theorem_query = mk_query(THEOREM_QUERY_SRC)
lemma_query = mk_query(LEMMA_QUERY_SRC)
decomp_query = mk_query(DECOMP_QUERY_SRC)
eval_query = mk_query(EVAL_QUERY_SRC)
opaque_query = mk_query(OPAQUE_QUERY_SRC)


def verify_node_to_req(node: Node) -> dict[str, str]:
    """Extract ImandraX request from a verify statement node."""
    req: dict[str, str] = {}
    assert node.type == 'verify_statement', 'not verify_statement'
    assert node.text, 'None text'
    verify_src = (
        node.text.decode('utf-8').strip().removeprefix('verify').strip()
    )
    # Remove parentheses
    if verify_src.startswith('(') and verify_src.endswith(')'):
        verify_src = verify_src[1:-1].strip()

    req['verify_src'] = verify_src
    return req


def instance_node_to_req(node: Node) -> dict[str, str]:
    """Extract ImandraX request from an instance statement node."""
    req: dict[str, str] = {}
    assert node.type == 'instance_statement', 'not instance_statement'
    assert node.text, 'None text'
    instance_src = (
        node.text.decode('utf-8').strip().removeprefix('instance').strip()
    )
    # Remove parentheses
    if instance_src.startswith('(') and instance_src.endswith(')'):
        instance_src = instance_src[1:-1].strip()
    req['instance_src'] = instance_src
    return req


def eval_node_to_src(node: Node) -> str:
    """Extract str from an eval statement node."""
    assert node.type == 'eval_statement', 'not eval_statement'
    assert node.text, 'None text'
    src = node.text.decode('utf-8').strip().removeprefix('eval').strip()
    # Remove parentheses
    if src.startswith('(') and src.endswith(')'):
        src = src[1:-1].strip()
    return src


class DecompParsingError(Exception):
    """Exception raised when parsing decomp fails."""

    pass


def decomp_capture_to_req(capture: dict[str, list[Node]]) -> dict[str, str]:
    """Extract ImandraX request from a decomp capture."""
    req: dict[str, str] = {}

    # Function name
    func_name = capture['func_name'][0].text
    assert func_name, 'No function name'
    req['func_name'] = func_name.decode('utf-8')

    # Decomp
    decomp_payload_node = capture['attribute_payload'][0]
    decomp_payload_b = decomp_payload_node.text
    assert decomp_payload_b, 'No decomp payload'
    req['decomp_payload'] = decomp_payload_b.decode('utf-8')

    req = req
    return req


def top_application_to_decomp(node: Node) -> dict[str, Any]:
    """Extract Decomp request request from a top application node."""
    assert node.type == 'application_expression'

    extract_top_arg_query = mk_query(r"""
    (application_expression
        (value_path
            (value_name) @top
            (#eq? @top "top")
        )
        (labeled_argument
            (label_name) @label
        ) @arg
        (unit)
    )
    """)

    matches = run_query(query=extract_top_arg_query, node=node)
    print(f'Found {len(matches)} labeled arguments')

    print(f'Matches: \n{matches}')

    res: dict[str, Any] = {}

    # Process each labeled argument based on its label
    for _, capture in matches:
        label_name_b = capture['label'][0].text
        assert label_name_b, 'Never: no label'
        label_name = label_name_b.decode('utf-8')
        arg_node = capture['arg'][0]

        match label_name:
            case 'assuming':
                # Parse assuming: ~assuming:[%id simple_branch]
                assuming_query = mk_query(r"""
                (extension
                    "[%"
                    (attribute_id) @attr_id
                    (attribute_payload) @payload
                    (#eq? @attr_id "id")
                )
                """)
                assuming_matches = run_query(
                    query=assuming_query, node=arg_node
                )
                if assuming_matches:
                    payload_text = assuming_matches[0][1]['payload'][0].text
                    assert payload_text, 'Never: no assuming payload'
                    res['assuming'] = payload_text.decode('utf-8')

            case 'basis' | 'rule_specs':
                # Query each extension separately to get all identifiers
                extension_query = mk_query(r"""
                (extension
                    "[%"
                    (attribute_id)
                    (attribute_payload
                        (expression_item
                            (value_path
                                (value_name) @id
                            )
                        )
                    )
                )
                """)
                extension_matches = run_query(
                    query=extension_query, node=arg_node
                )
                if extension_matches:
                    ids: list[str] = []
                    for match in extension_matches:
                        id_node = match[1]['id'][0]
                        id_text = id_node.text
                        assert id_text, f'Never: no {label_name} id text'
                        ids.append(id_text.decode('utf-8'))
                    res[label_name] = ids

            case 'prune' | 'ctx_simp':
                # Parse boolean: ~prune:true
                bool_query = mk_query(r"""
                (boolean) @bool_val
                """)
                bool_matches = run_query(query=bool_query, node=arg_node)
                if bool_matches:
                    bool_text = bool_matches[0][1]['bool_val'][0].text
                    assert bool_text, f'Never: no {label_name} boolean text'
                    res[label_name] = bool_text.decode('utf-8') == 'true'

            case 'lift_bool':
                # Parse constructor: ~lift_bool:Default
                constructor_query = mk_query(r"""
                (constructor_path
                    (constructor_name) @constructor
                )
                """)
                constructor_matches = run_query(
                    query=constructor_query, node=arg_node
                )
                if constructor_matches:
                    constructor_text = constructor_matches[0][1]['constructor'][
                        0
                    ].text
                    assert constructor_text, (
                        'Never: no lift_bool constructor text'
                    )
                    lift_bool_value = constructor_text.decode('utf-8')
                    lift_bool_enum = [
                        'Default',
                        'Nested_equalities',
                        'Equalities',
                        'All',
                    ]
                    if lift_bool_value not in lift_bool_enum:
                        raise DecompParsingError(
                            f'Invalid lift_bool value: {lift_bool_value}',
                            f'should be one of {lift_bool_enum}',
                        )
                    res['lift_bool'] = lift_bool_value
            case _:
                assert 'False', 'Never'

    return res
