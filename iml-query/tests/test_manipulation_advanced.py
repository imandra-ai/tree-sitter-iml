# pyright: basic
from inline_snapshot import snapshot

from iml_query.queries import (
    DECOMP_QUERY_SRC,
    VERIFY_QUERY_SRC,
)
from iml_query.tree_sitter_utils import (
    delete_nodes,
    get_nesting_relationship,
    get_parser,
    mk_query,
    run_query,
    unwrap_byte,
)


def test_delete_nodes_multiple():
    """Test deleting multiple nodes from IML code."""
    iml = """\
let add_one (x: int) : int = x + 1

verify (fun x -> x > 0 ==> double x > x)

let is_positive (x: int) : bool = x > 0

verify double_non_negative_is_increasing

let double (x: int) : int = x * 2

verify (fun y -> y < 0 ==> double y < y)
"""
    parser = get_parser(ocaml=False)
    tree = parser.parse(bytes(iml, encoding='utf8'))

    # Find all verify statements
    matches = run_query(mk_query(VERIFY_QUERY_SRC), node=tree.root_node)
    verify_nodes = [capture['verify'][0] for _, capture in matches]

    # Delete all verify statements
    new_iml, _new_tree = delete_nodes(iml, tree, nodes=verify_nodes)
    assert new_iml == snapshot("""\
let add_one (x: int) : int = x + 1



let is_positive (x: int) : bool = x > 0



let double (x: int) : int = x * 2


""")


def test_delete_nodes_single():
    """Test deleting a single node."""
    iml = """\
let simple_branch x =
  if x = 1 || x = 2 then x + 1 else x - 1
[@@decomp top ()]

let f x = x + 1
"""
    parser = get_parser(ocaml=False)
    tree = parser.parse(bytes(iml, encoding='utf8'))

    # Find decomp attribute
    matches = run_query(mk_query(DECOMP_QUERY_SRC), node=tree.root_node)
    decomp_attr = matches[0][1]['decomp_attr'][0]

    # Delete the decomp attribute
    new_iml, _new_tree = delete_nodes(iml, tree, nodes=[decomp_attr])
    assert new_iml == snapshot("""\
let simple_branch x =
  if x = 1 || x = 2 then x + 1 else x - 1


let f x = x + 1
""")


def test_delete_nodes_empty_list():
    """Test delete_nodes with empty list."""
    iml = """\
let f x = x + 1
let g y = y * 2
"""
    parser = get_parser(ocaml=False)
    tree = parser.parse(bytes(iml, encoding='utf8'))

    # Delete no nodes
    new_iml, _new_tree = delete_nodes(iml, tree, nodes=[])
    assert new_iml == iml  # Should be unchanged


def test_get_nesting_relationship():
    """Test nesting relationship detection with complex nested structure."""
    iml = """\
let triple_nested (f : int list) (i : int) (n : int) : int list =
  let rec outer_helper curr_f curr_i =
    let rec inner_helper curr_f curr_i =
      if curr_i > n then
        curr_f
      else
        let rec deepest_helper x =
          if x = 0 then curr_f
          else deepest_helper (x - 1)
        [@@measure Ordinal.of_int x]
        in
        deepest_helper curr_i
    [@@measure Ordinal.of_int (n - curr_i)]
    in
    inner_helper curr_f curr_i
  [@@measure Ordinal.of_int (n - curr_i)]
  in
  outer_helper f i

let top_level_function x = x + 1
[@@measure Ordinal.of_int 1]
"""
    parser = get_parser(ocaml=False)
    tree = parser.parse(bytes(iml, encoding='utf8'))

    # Find all value definitions
    value_def_query = mk_query(r"""
    (value_definition
        (let_binding
            pattern: (value_name) @func_name
        )
    ) @function
    """)

    matches = run_query(value_def_query, node=tree.root_node)

    # Build a map of function names to nodes
    functions = {}
    for _, capture in matches:
        func_name = unwrap_byte(capture['func_name'][0].text).decode('utf-8')
        func_node = capture['function'][0]
        functions[func_name] = func_node

    # Test various nesting relationships
    triple_nested = functions['triple_nested']
    top_level = functions['top_level_function']

    # Find all nested functions
    nested_funcs = []
    for name, node in functions.items():
        if name not in ['triple_nested', 'top_level_function']:
            nested_funcs.append((name, node))

    # Test nesting levels
    relationships = {}
    for name, nested_node in nested_funcs:
        # Test relationship to triple_nested
        level_to_triple = get_nesting_relationship(nested_node, triple_nested)
        # Test relationship to top_level (should be -1, not nested)
        level_to_top = get_nesting_relationship(nested_node, top_level)
        # Test relationship to itself (should be 0)
        level_to_self = get_nesting_relationship(nested_node, nested_node)

        relationships[name] = {
            'to_triple_nested': level_to_triple,
            'to_top_level': level_to_top,
            'to_self': level_to_self,
        }

    assert relationships == snapshot(
        {
            'outer_helper': {
                'to_triple_nested': 1,
                'to_top_level': -1,
                'to_self': 0,
            },
            'inner_helper': {
                'to_triple_nested': 2,
                'to_top_level': -1,
                'to_self': 0,
            },
            'deepest_helper': {
                'to_triple_nested': 3,
                'to_top_level': -1,
                'to_self': 0,
            },
        }
    )


def test_complex_decomp_with_composition():
    """Test complex decomp parsing with composition operators."""
    iml = """\
let base_function x =
  if x mod 3 = 0 then 0
  else if x mod 3 = 1 then 1
  else 2
[@@decomp top ()]

let dependent_function x =
  let base_result = base_function x in
  if base_result = 0 then x / 3
  else if base_result = 1 then x + 1
  else x - 1

let merged_decomposition = dependent_function
[@@decomp top ~basis:[[%id base_function]] () << top () [%id base_function]]

let compound_merged = dependent_function
[@@decomp top ~basis:[[%id base_function]] () <|< top () [%id base_function]]

let redundant_regions x =
  if x > 0 then 1
  else if x < -10 then 1
  else if x = 0 then 0
  else 1
[@@decomp ~| (top ())]
"""
    parser = get_parser(ocaml=False)
    tree = parser.parse(bytes(iml, encoding='utf8'))

    # Find all decomp attributes
    matches = run_query(mk_query(DECOMP_QUERY_SRC), node=tree.root_node)

    # Count how many decomp attributes we found
    decomp_count = len(matches)
    assert decomp_count == snapshot(4)

    # Test that we can identify the function names
    func_names = []
    for _, capture in matches:
        if 'decomposed_func_name' in capture:
            name = unwrap_byte(capture['decomposed_func_name'][0].text).decode(
                'utf-8'
            )
            func_names.append(name)

    assert func_names == snapshot(
        [
            'base_function',
            'merged_decomposition',
            'compound_merged',
            'redundant_regions',
        ]
    )


def test_edge_cases_empty_content():
    """Test edge cases with minimal or empty content."""
    # Test with just comments
    iml_comments = """\
(* This is just a comment *)
(* Another comment *)
"""
    parser = get_parser(ocaml=False)
    tree = parser.parse(bytes(iml_comments, encoding='utf8'))

    # Should find no verify statements
    matches = run_query(mk_query(VERIFY_QUERY_SRC), node=tree.root_node)
    assert len(matches) == 0

    # Test with just a simple expression
    iml_simple = 'let x = 42'
    tree_simple = parser.parse(bytes(iml_simple, encoding='utf8'))
    matches_simple = run_query(
        mk_query(VERIFY_QUERY_SRC), node=tree_simple.root_node
    )
    assert len(matches_simple) == 0
