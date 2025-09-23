# pyright: basic
from inline_snapshot import snapshot

from iml_query.tree_sitter_utils import (
    get_nesting_relationship,
    get_parser,
    mk_query,
    run_query,
    unwrap_byte,
)


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
