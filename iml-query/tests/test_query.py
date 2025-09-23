from inline_snapshot import snapshot
from rich.pretty import Pretty

from iml_query.processing import find_nested_measures
from iml_query.queries import (
    DECOMP_QUERY_SRC,
    VERIFY_QUERY_SRC,
)
from iml_query.tree_sitter_utils import (
    get_parser,
    mk_query,
    run_query,
    unwrap_byte,
)
from iml_query.utils import get_rich_str


def test_find_nested_measures():
    iml = """\
let build_fib (f : int list) (i : int) (n : int) : int list =
let rec helper curr_f curr_i =
    if curr_i > n then
    curr_f
    else
    match (List.nth (curr_i - 1) curr_f, List.nth (curr_i - 2) curr_f) with
    | (Some prev1, Some prev2) ->
        let new_f = curr_f @ [prev1 + prev2] in
        helper new_f (curr_i + 1)
    | _ -> curr_f
[@@measure Ordinal.of_int (n - curr_i)]
in
helper f i


let good_measure x =
x + 1
[@@measure Ordinal.of_int 1]


let triple_nested (f : int list) (i : int) (n : int) : int list =
let rec helper curr_f curr_i =
    let rec helper curr_f curr_i =
    if curr_i > n then
        curr_f
    else
        match (List.nth (curr_i - 1) curr_f, List.nth (curr_i - 2) curr_f) with
        | (Some prev1, Some prev2) ->
            let new_f = curr_f @ [prev1 + prev2] in
            helper new_f (curr_i + 1)
        | _ -> curr_f
    [@@measure Ordinal.of_int (n - curr_i)]
    in
    helper f i
in
helper f i\
"""
    parser = get_parser()
    tree = parser.parse(bytes(iml, encoding='utf8'))
    problematic_funcs = find_nested_measures(tree.root_node)
    assert len(problematic_funcs) == 2
    assert get_rich_str(Pretty(problematic_funcs)) == snapshot("""\
[
    {
        'top_level_function_name': 'build_fib',
        'node': <Node type=value_definition, start_point=(0, 0), end_point=(12, \n\
10)>,
        'range': <Range start_point=(0, 0), end_point=(12, 10), start_byte=0, \n\
end_byte=399>,
        'nested_measures': [
            {
                'function_name': 'helper',
                'level': 1,
                'range': <Range start_point=(1, 0), end_point=(10, 39), \n\
start_byte=62, end_byte=385>,
                'node': <Node type=value_definition, start_point=(1, 0), \n\
end_point=(10, 39)>
            }
        ]
    },
    {
        'top_level_function_name': 'triple_nested',
        'node': <Node type=value_definition, start_point=(20, 0), end_point=(35,
10)>,
        'range': <Range start_point=(20, 0), end_point=(35, 10), start_byte=460,
end_byte=948>,
        'nested_measures': [
            {
                'function_name': 'helper',
                'level': 2,
                'range': <Range start_point=(22, 4), end_point=(31, 43), \n\
start_byte=561, end_byte=912>,
                'node': <Node type=value_definition, start_point=(22, 4), \n\
end_point=(31, 43)>
            }
        ]
    }
]\
""")  # noqa: E501


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
    parser = get_parser()
    tree = parser.parse(bytes(iml, encoding='utf8'))

    # Find all decomp attributes
    matches = run_query(mk_query(DECOMP_QUERY_SRC), node=tree.root_node)

    # Count how many decomp attributes we found
    decomp_count = len(matches)
    assert decomp_count == snapshot(4)

    # Test that we can identify the function names
    func_names: list[str] = []
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
    parser = get_parser()
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
