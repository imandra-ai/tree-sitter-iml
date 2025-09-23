from inline_snapshot import snapshot
from rich.pretty import Pretty

from iml_query.query.query import (
    find_nested_measures,
)
from iml_query.tree_sitter_utils import get_parser
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
    parser = get_parser(ocaml=False)
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
