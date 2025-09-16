from typing import cast

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

# [@@@import Mod_name, "path/to/file.iml"] (path import with explicit module name)
# [@@@import Mod_name, "path/to/file.iml", Mod_name2] (same, with explicit extraction name)
# [@@@import "path/to/file.iml"] (path import as module `File`)
# [@@@import Mod_name, "findlib:foo.bar"] (import from ocamlfind library)
# [@@@import Mod_name, "findlib:foo.bar", Mod_name2] (same, with explicit extraction name)
# [@@@import Mod_name, "dune:foo.bar"] (import from dune library)
# [@@@import Mod_name, "dune:foo.bar", Mod_name2] (same, with explicit extraction name)

IMPORT_QUERY_SRC = r"""
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

verify_query = Query(iml_language, VERIFY_QUERY_SRC)
instance_query = Query(iml_language, INSTANCE_QUERY_SRC)
axiom_query = Query(iml_language, AXIOM_QUERY_SRC)
theorem_query = Query(iml_language, THEOREM_QUERY_SRC)
lemma_query = Query(iml_language, LEMMA_QUERY_SRC)
decomp_query = Query(iml_language, DECOMP_QUERY_SRC)
eval_query = Query(iml_language, EVAL_QUERY_SRC)
opaque_query = Query(iml_language, OPAQUE_QUERY_SRC)
import_query = Query(iml_language, IMPORT_QUERY_SRC)


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


def decomp_capture_to_req(capture: dict[str, list[Node]]) -> dict[str, str]:
    """Extract ImandraX request from a decomp capture."""
    req: dict[str, str] = {}

    # Function name
    func_name = capture['func_name'][0].text
    assert func_name, 'No function name'
    req['func_name'] = func_name.decode('utf-8')

    # Decomp
    decomp_payload = capture['attribute_payload'][0].text
    assert decomp_payload, 'No decomp payload'
    req['decomp_payload'] = decomp_payload.decode('utf-8')

    req = req
    return req


# query on application expression
TOP_QUERY = r"""

"""


def top_application_to_decomp(node: Node) -> dict[str, str]:
    node.children[0].text == 'top'

    pass
