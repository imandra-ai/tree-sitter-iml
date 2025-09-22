from typing import Any, cast, overload

import structlog
from tree_sitter import Node, Query, QueryCursor, Tree

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
    """Run a Tree-sitter query on the given code or node.

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


def unwrap_byte(node_text: bytes | None) -> bytes:
    if node_text is None:
        raise ValueError('Node text is None')
    return node_text


# =====
# Queries and node transformation
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

    req['src'] = verify_src
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
    req['src'] = instance_src
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
    # print(f'Found {len(matches)} labeled arguments')

    # print(f'Matches: \n{matches}')

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

    default_res: dict[str, Any] = {
        'basis': [],
        'rule_specs': [],
        'prune': False,
    }

    res = default_res | res

    return res


def decomp_attribute_payload_to_decomp_req_labels(node: Node) -> dict[str, Any]:
    assert node.type == 'attribute_payload'

    expect_appl = node.children[0].children[0]
    if expect_appl.type != 'application_expression':
        raise NotImplementedError('Composition operators are not supported yet')

    return top_application_to_decomp(expect_appl)


# ======
# Extract
# ======


@overload
def delete_nodes(
    nodes: list[Node],
    iml: str,
    old_tree: Tree,
) -> tuple[str, Tree]: ...


@overload
def delete_nodes(
    nodes: list[Node],
    iml: str,
) -> tuple[str, None]: ...


def delete_nodes(
    nodes: list[Node],
    iml: str,
    old_tree: Tree | None = None,
) -> tuple[str, Tree | None]:
    """Delete nodes from IML string and return updated string and tree.

    Return new tree if old_tree is provided.

    Arguments:
        nodes: list of nodes to delete
        iml: old IML code
        old_tree: old parsed tree

    """
    if not nodes:
        return iml, old_tree

    # Extract byte ranges from nodes
    edits = [node.byte_range for node in nodes]

    # Check for overlapping edits
    sorted_edits = sorted(edits, key=lambda x: x[0])
    for i in range(len(sorted_edits) - 1):
        curr_end = sorted_edits[i][1]
        next_start = sorted_edits[i + 1][0]
        if curr_end > next_start:
            raise ValueError(
                f'Overlapping nodes: positions {sorted_edits[i]} and '
                f'{sorted_edits[i + 1]}'
            )

    # Apply tree edits if we have an old tree
    if old_tree is not None:
        # Sort nodes by start position for tree editing
        sorted_nodes = sorted(nodes, key=lambda x: x.start_byte)

        # Apply tree edits in forward order
        for node in sorted_nodes:
            old_tree.edit(
                start_byte=node.start_byte,
                old_end_byte=node.end_byte,
                new_end_byte=node.start_byte,
                start_point=node.start_point,
                old_end_point=node.end_point,
                new_end_point=node.start_point,
            )

    # Apply deletions to text in reverse order to avoid offset issues
    edits_reversed = sorted(edits, key=lambda x: x[0], reverse=True)
    iml_b = bytes(iml, encoding='utf8')
    for start, end in edits_reversed:
        iml_b = iml_b[:start] + iml_b[end:]
    iml = iml_b.decode('utf8')

    # Get new tree
    if old_tree is not None:
        parser = get_parser(ocaml=False)
        new_tree = parser.parse(iml_b, old_tree=old_tree)
    else:
        new_tree = None

    return iml, new_tree


def extract_opaque_function_names(iml: str) -> list[str]:
    opaque_functions: list[str] = []
    matches = run_query(mk_query(OPAQUE_QUERY_SRC), iml)
    for _, capture in matches:
        value_name_node = capture['func_name'][0]
        func_name = unwrap_byte(value_name_node.text).decode('utf-8')
        opaque_functions.append(func_name)

    return opaque_functions


def extract_verify_reqs(
    iml: str, tree: Tree
) -> tuple[str, Tree, list[dict[str, Any]]]:
    root = tree.root_node
    matches = run_query(
        mk_query(VERIFY_QUERY_SRC),
        node=root,
    )

    reqs: list[dict[str, Any]] = []
    nodes_to_delete: list[Node] = []

    for _, capture in matches:
        verify_statement_node = capture['verify'][0]
        nodes_to_delete.append(verify_statement_node)
        reqs.append(verify_node_to_req(verify_statement_node))

    new_iml, new_tree = delete_nodes(nodes_to_delete, iml, tree)
    return new_iml, new_tree, reqs


def extract_instance_reqs(
    iml: str, tree: Tree
) -> tuple[str, Tree, list[dict[str, Any]]]:
    root = tree.root_node
    matches = run_query(
        mk_query(INSTANCE_QUERY_SRC),
        node=root,
    )

    reqs: list[dict[str, Any]] = []
    nodes_to_delete: list[Node] = []

    for _, capture in matches:
        instance_statement_node = capture['instance'][0]
        nodes_to_delete.append(instance_statement_node)
        reqs.append(instance_node_to_req(instance_statement_node))

    new_iml, new_tree = delete_nodes(nodes_to_delete, iml, tree)
    return new_iml, new_tree, reqs


def extract_decomp_reqs(
    iml: str, tree: Tree
) -> tuple[str, Tree, list[dict[str, Any]]]:
    root = tree.root_node
    matches = run_query(
        mk_query(DECOMP_QUERY_SRC),
        node=root,
    )

    reqs: list[dict[str, Any]] = []
    nodes_to_delete: list[Node] = []

    for _, capture in matches:
        decomp_attr_node = capture['decomp_attr'][0]
        nodes_to_delete.append(decomp_attr_node)

        req: dict[str, Any] = {}
        req['name'] = unwrap_byte(
            capture['decomposed_func_name'][0].text
        ).decode('utf8')
        req_labels = decomp_attribute_payload_to_decomp_req_labels(
            capture['decomp_payload'][0]
        )
        req |= req_labels
        reqs.append(req)

    new_iml, new_tree = delete_nodes(nodes_to_delete, iml, tree)
    return new_iml, new_tree, reqs


def iml_outline(iml: str) -> dict[str, Any]:
    outline: dict[str, Any] = {}
    tree = get_parser(ocaml=False).parse(bytes(iml, encoding='utf8'))
    outline['verify_req'] = extract_verify_reqs(iml, tree)[2]
    outline['instance_req'] = extract_instance_reqs(iml, tree)[2]
    outline['decompose_req'] = extract_decomp_reqs(iml, tree)[2]
    outline['opaque_function'] = extract_opaque_function_names(iml)
    return outline
