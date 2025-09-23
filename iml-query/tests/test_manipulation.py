from inline_snapshot import snapshot

from iml_query.query.query import (
    decomp_req_to_top_appl_text,
    extract_decomp_reqs,
    find_func_definition,
    insert_decomp_req,
    insert_lines,
)
from iml_query.tree_sitter_utils import get_parser


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
    parser = get_parser(ocaml=False)
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
