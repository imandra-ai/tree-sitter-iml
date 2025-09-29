from inline_snapshot import snapshot

from iml_query.processing import (
    decomp_req_to_top_appl_text,
    extract_decomp_reqs,
    extract_verify_reqs,
    find_func_definition,
    insert_decomp_req,
    insert_verify_req,
)
from iml_query.queries import (
    DECOMP_QUERY_SRC,
    VERIFY_QUERY_SRC,
)
from iml_query.tree_sitter_utils import (
    delete_nodes,
    get_parser,
    insert_lines,
    mk_query,
    run_query,
)


def test_manipualtion_decomp():
    iml = """
    let simple_branch x =\
    if x = 1 || x = 2 then x + 1 else x - 1
    [@@decomp top ()]


    let f x = x + 1

    let simple_branch2  = simple_branch
    [@@decomp top ~assuming:[%id simple_branch] ~basis:[[%id simple_branch] ; [%id f]] ~rule_specs:[[%id simple_branch]] ~prune:true ~ctx_simp:true ~lift_bool: Default ()]

    let simple_branch3 x =
    if x = 1 || x = 2 then x + 1 else x - 1
    [@@decomp top ~prune: true ()]\
    """  # noqa: E501
    parser = get_parser()
    tree = parser.parse(bytes(iml, encoding='utf8'))

    # %%
    iml2, tree2, decomp_reqs = extract_decomp_reqs(iml, tree)
    assert decomp_reqs == snapshot(
        [
            {
                'name': 'simple_branch',
                'basis': [],
                'rule_specs': [],
                'prune': False,
            },
            {
                'name': 'simple_branch2',
                'basis': ['simple_branch', 'f'],
                'rule_specs': ['simple_branch'],
                'prune': True,
                'assuming': 'simple_branch',
                'ctx_simp': True,
                'lift_bool': 'Default',
            },
            {
                'name': 'simple_branch3',
                'basis': [],
                'rule_specs': [],
                'prune': True,
            },
        ]
    )

    # %%
    decomp_req_2 = decomp_reqs[1]

    assert decomp_req_to_top_appl_text(decomp_req_2) == snapshot(
        'top ~basis:[[%id simple_branch] ; [%id f]] ~rule_specs:[[%id simple_branch]] ~prune:true ~assuming:[%id s] ~ctx_simp:true ()]'  # noqa: E501
    )

    # %%
    func_def = find_func_definition(tree2, 'simple_branch2')
    assert repr(func_def) == snapshot(
        '<Node type=value_definition, start_point=(7, 4), end_point=(7, 39)>'
    )
    assert str(func_def) == snapshot(
        '(value_definition (let_binding pattern: (value_name) body: (value_path (value_name))))'  # noqa: E501
    )

    # %%
    top_2 = decomp_req_to_top_appl_text(decomp_reqs[1])
    lines = [f'[@@decomp {top_2}]']

    iml3, _tree3 = insert_lines(iml2, tree2, lines=lines, insert_after=7)

    assert iml3 == snapshot("""\

    let simple_branch x =    if x = 1 || x = 2 then x + 1 else x - 1
    \n\


    let f x = x + 1

    let simple_branch2  = simple_branch
[@@decomp top ~basis:[[%id simple_branch] ; [%id f]] ~rule_specs:[[%id simple_branch]] ~prune:true ~assuming:[%id s] ~ctx_simp:true ()]]
    \n\

    let simple_branch3 x =
    if x = 1 || x = 2 then x + 1 else x - 1
        \
""")  # noqa: E501

    # %%
    iml4, _tree4 = insert_decomp_req(iml2, tree2, decomp_req_2)
    assert iml4 == snapshot("""\

    let simple_branch x =    if x = 1 || x = 2 then x + 1 else x - 1
    \n\


    let f x = x + 1

    let simple_branch2  = simple_branch
[@@decomp top ~basis:[[%id simple_branch] ; [%id f]] ~rule_specs:[[%id simple_branch]] ~prune:true ~assuming:[%id s] ~ctx_simp:true ()]]
    \n\

    let simple_branch3 x =
    if x = 1 || x = 2 then x + 1 else x - 1
        \
""")  # noqa: E501

    # %%
    assert iml3 == iml4


def test_manipulation_verify():
    iml = """\
let add_one (x: int) : int = x + 1

let is_positive (x: int) : bool = x > 0

let double (x: int) : int = x * 2

verify (fun x -> x > 0 ==> double x > x)

let double_non_negative_is_increasing (x: int) = x >= 0 ==> double x > x

verify double_non_negative_is_increasing\
"""
    parser = get_parser()
    tree = parser.parse(bytes(iml, encoding='utf8'))

    # %%
    iml2, tree2, verify_reqs = extract_verify_reqs(iml, tree)
    assert verify_reqs == snapshot(
        [
            {'src': 'fun x -> x > 0 ==> double x > x'},
            {'src': 'double_non_negative_is_increasing'},
        ]
    )

    # %%
    assert iml2 == snapshot("""\
let add_one (x: int) : int = x + 1

let is_positive (x: int) : bool = x > 0

let double (x: int) : int = x * 2



let double_non_negative_is_increasing (x: int) = x >= 0 ==> double x > x

""")

    # %%
    iml3, _tree3 = insert_verify_req(iml2, tree2, verify_reqs[0]['src'])
    assert iml3 == snapshot("""\
let add_one (x: int) : int = x + 1

let is_positive (x: int) : bool = x > 0

let double (x: int) : int = x * 2



let double_non_negative_is_increasing (x: int) = x >= 0 ==> double x > x

verify (fun x -> x > 0 ==> double x > x)
""")

    # %%
    iml4, _tree4 = insert_verify_req(iml3, tree2, verify_reqs[1]['src'])
    assert iml4 == snapshot("""\
let add_one (x: int) : int = x + 1

let is_positive (x: int) : bool = x > 0

let double (x: int) : int = x * 2



let double_non_negative_is_increasing (x: int) = x >= 0 ==> double x > x

verify (fun x -> x > 0 ==> double x > x)
verify (double_non_negative_is_increasing)
""")


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
    parser = get_parser()
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
    parser = get_parser()
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
    parser = get_parser()
    tree = parser.parse(bytes(iml, encoding='utf8'))

    # Delete no nodes
    new_iml, _new_tree = delete_nodes(iml, tree, nodes=[])
    assert new_iml == iml  # Should be unchanged
