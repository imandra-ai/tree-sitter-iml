import pytest
from inline_snapshot import snapshot

from iml_query.processing import (
    Nesting,
    eval_capture_to_src,
    extract_decomp_reqs,
    extract_instance_reqs,
    extract_opaque_function_names,
    find_nested_rec,
    iml_outline,
    insert_instance_req,
    instance_capture_to_req,
    update_top_definition,
    verify_capture_to_req,
)
from iml_query.queries import (
    EVAL_QUERY_SRC,
    INSTANCE_QUERY_SRC,
    VERIFY_QUERY_SRC,
    EvalCapture,
    InstanceCapture,
    VerifyCapture,
)
from iml_query.tree_sitter_utils import (
    get_parser,
    mk_query,
    run_queries,
    run_query,
    unwrap_bytes,
)


def test_verify_node_to_req():
    """Test verify_node_to_req with various verify statement formats."""
    iml = """\
verify (fun x -> x > 0 ==> double x > x)

verify double_non_negative_is_increasing

verify (
  fun xs ys i ->
    let a, _ = (fulcrum_inner xs ys i) in a >= i
)
"""
    parser = get_parser()
    tree = parser.parse(bytes(iml, encoding='utf8'))
    matches = run_query(mk_query(VERIFY_QUERY_SRC), node=tree.root_node)

    reqs = [
        verify_capture_to_req(VerifyCapture.from_ts_capture(capture))
        for _, capture in matches
    ]
    assert reqs == snapshot(
        [
            {'src': 'fun x -> x > 0 ==> double x > x'},
            {'src': 'double_non_negative_is_increasing'},
            {
                'src': """\
fun xs ys i ->
    let a, _ = (fulcrum_inner xs ys i) in a >= i\
"""
            },
        ]
    )


def test_instance_node_to_req():
    """Test instance_node_to_req with instance statements."""
    iml = """\
instance (fun x -> x > 0 && x < 10)

instance some_predicate

instance (
  fun x y ->
    x + y > 0 &&
    x * y < 100
)
"""
    parser = get_parser()
    tree = parser.parse(bytes(iml, encoding='utf8'))
    matches = run_query(mk_query(INSTANCE_QUERY_SRC), node=tree.root_node)

    reqs = [
        instance_capture_to_req(InstanceCapture.from_ts_capture(capture))
        for _, capture in matches
    ]
    assert reqs == snapshot(
        [
            {'src': 'fun x -> x > 0 && x < 10'},
            {'src': 'some_predicate'},
            {
                'src': """\
fun x y ->
    x + y > 0 &&
    x * y < 100\
"""
            },
        ]
    )


def test_eval_node_to_src():
    """Test eval_node_to_src with eval statements."""
    iml = """\
eval (1 + 2 * 3)

eval some_function 42

eval (
  let x = 5 in
  let y = 10 in
  x + y
)
"""
    parser = get_parser()
    tree = parser.parse(bytes(iml, encoding='utf8'))
    matches = run_queries(
        queries={'eval': EVAL_QUERY_SRC},
        node=tree.root_node,
    )

    eval_captures = [
        EvalCapture.from_ts_capture(capture) for capture in matches['eval']
    ]

    srcs = [eval_capture_to_src(cap) for cap in eval_captures]
    assert srcs == snapshot(
        [
            '1 + 2 * 3',
            'some_function 42',
            """\
let x = 5 in
  let y = 10 in
  x + y\
""",
        ]
    )


def test_extract_opaque_function_names():
    """Test extracting opaque function names from decomp examples."""
    iml = """\
let expensive_computation x = x * x * x + 2 * x + 1
[@@opaque]

let external_api_call x = if x mod 2 = 0 then x / 2 else 3 * x + 1
[@@opaque]

let normal_function x = x + 1

let another_opaque_fn y z = y * z
[@@opaque]
"""
    opaque_functions = extract_opaque_function_names(iml)
    assert opaque_functions == snapshot(
        ['expensive_computation', 'external_api_call', 'another_opaque_fn']
    )


def test_extract_instance_reqs():
    """Test extracting instance requests and removing them from code."""
    iml = """\
let add_one (x: int) : int = x + 1

instance (fun x -> x > 0)

let is_positive (x: int) : bool = x > 0

instance positive_checker

let double (x: int) : int = x * 2

instance (fun x y -> x + y > 0 && x - y < 10)
"""
    parser = get_parser()
    tree = parser.parse(bytes(iml, encoding='utf8'))

    new_iml, _new_tree, instance_reqs = extract_instance_reqs(iml, tree)

    assert instance_reqs == snapshot(
        [
            {'src': 'fun x -> x > 0'},
            {'src': 'positive_checker'},
            {'src': 'fun x y -> x + y > 0 && x - y < 10'},
        ]
    )
    assert new_iml == snapshot("""\
let add_one (x: int) : int = x + 1



let is_positive (x: int) : bool = x > 0



let double (x: int) : int = x * 2


""")


def test_insert_instance_req():
    """Test inserting instance requests back into code."""
    iml = """\
let add_one (x: int) : int = x + 1

let is_positive (x: int) : bool = x > 0

let double (x: int) : int = x * 2
"""
    parser = get_parser()
    tree = parser.parse(bytes(iml, encoding='utf8'))

    # Insert first instance
    new_iml, new_tree = insert_instance_req(iml, tree, 'fun x -> x > 0')
    assert new_iml == snapshot("""\
let add_one (x: int) : int = x + 1

let is_positive (x: int) : bool = x > 0

let double (x: int) : int = x * 2
instance (fun x -> x > 0)
""")

    # Insert second instance
    final_iml, _final_tree = insert_instance_req(
        new_iml, new_tree, 'positive_checker'
    )
    assert final_iml == snapshot("""\
let add_one (x: int) : int = x + 1

let is_positive (x: int) : bool = x > 0

let double (x: int) : int = x * 2
instance (fun x -> x > 0)
instance (positive_checker)
""")


def test_iml_outline():
    """Test iml_outline with all request types and opaque functions."""
    iml = """\
let expensive_computation x = x * x * x + 2 * x + 1
[@@opaque]

let simple_branch x =
  if x = 1 || x = 2 then x + 1 else x - 1
[@@decomp top ()]

let f x = x + 1

let simple_branch2 = simple_branch
[@@decomp top ~assuming:[%id simple_branch] ~basis:[[%id simple_branch] ; [%id f]] ~rule_specs:[[%id simple_branch]] ~prune:true ~ctx_simp:true ~lift_bool:Default ()]

verify (fun x -> x > 0 ==> double x > x)

instance (fun x -> x > 0)

let external_api_call x = if x mod 2 = 0 then x / 2 else 3 * x + 1
[@@opaque]

verify double_non_negative_is_increasing

instance positive_predicate\
"""  # noqa: E501
    outline = iml_outline(iml)
    assert outline == snapshot(
        {
            'verify_req': [
                {'src': 'fun x -> x > 0 ==> double x > x'},
                {'src': 'double_non_negative_is_increasing'},
            ],
            'instance_req': [
                {'src': 'fun x -> x > 0'},
                {'src': 'positive_predicate'},
            ],
            'decompose_req': [
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
            ],
            'opaque_function': ['expensive_computation', 'external_api_call'],
        }
    )


def test_complex_decomp_parsing_detailed():
    """Test detailed parsing of complex decomp examples from decomp_eg2.iml."""
    iml = """\
let expensive_computation x = x * x * x + 2 * x + 1
let external_api_call x = if x mod 2 = 0 then x / 2 else 3 * x + 1

let business_logic x y =
  let result1 = expensive_computation x in
  let result2 = external_api_call y in
  if result1 > result2 then result1 - result2
  else result2 - result1
[@@decomp top ~basis:[[%id expensive_computation]; [%id external_api_call]] ()]

let context_sensitive x y z =
  if x = y then
    if x <> z then x + 1
    else x * 2
  else
    if y = z then y - 1
    else x + y + z
[@@decomp top ~ctx_simp:true ()]
"""

    parser = get_parser()
    tree = parser.parse(bytes(iml, encoding='utf8'))
    _, _, decomp_reqs = extract_decomp_reqs(iml, tree)

    assert decomp_reqs == snapshot(
        [
            {
                'name': 'business_logic',
                'basis': ['expensive_computation', 'external_api_call'],
                'rule_specs': [],
                'prune': False,
            },
            {
                'name': 'context_sensitive',
                'basis': [],
                'rule_specs': [],
                'prune': False,
                'ctx_simp': True,
            },
        ]
    )


@pytest.mark.xfail
def test_composition_operator_decomp_parsing():
    """Test detailed parsing of complex decomp examples from decomp_eg2.iml."""
    iml = """\
let expensive_computation x = x * x * x + 2 * x + 1
let external_api_call x = if x mod 2 = 0 then x / 2 else 3 * x + 1

let business_logic x y =
  let result1 = expensive_computation x in
  let result2 = external_api_call y in
  if result1 > result2 then result1 - result2
  else result2 - result1
[@@decomp top ~basis:[[%id expensive_computation]; [%id external_api_call]] ()]

let infeasible_branches x =
  if x > 10 && x < 5 then 999
  else if x = 0 then 0
  else if x > 0 then x
  else -x
[@@decomp top () |>> prune]
"""

    parser = get_parser()
    tree = parser.parse(bytes(iml, encoding='utf8'))
    _, _, _decomp_reqs = extract_decomp_reqs(iml, tree)


def test_mixed_requests_extraction():
    """Test extraction of mixed request types."""
    iml = """\
let rec sum (xs : int list) : int =
    match xs with
    | [] -> 0
    | x :: xs' -> x + sum xs'

verify (fun xs -> List.length xs >= 0)

let helper_function x = x * 2
[@@opaque]

instance (fun x -> x > 0 && x < 100)

let conditional_fn y =
  if y > 10 then y else 0
[@@decomp top ~prune:true ()]

verify (fun ys ->
   let i = sum ys in
      i >= 0
)
"""
    from iml_query.processing import (
        extract_decomp_reqs,
        extract_instance_reqs,
        extract_opaque_function_names,
        extract_verify_reqs,
    )

    parser = get_parser()
    tree = parser.parse(bytes(iml, encoding='utf8'))

    # Test each extraction function individually
    _, _, verify_reqs = extract_verify_reqs(iml, tree)
    _, _, instance_reqs = extract_instance_reqs(iml, tree)
    _, _, decomp_reqs = extract_decomp_reqs(iml, tree)
    opaque_funcs = extract_opaque_function_names(iml)

    combined_results = {
        'verify_reqs': verify_reqs,
        'instance_reqs': instance_reqs,
        'decomp_reqs': decomp_reqs,
        'opaque_functions': opaque_funcs,
    }

    assert combined_results == snapshot(
        {
            'verify_reqs': [
                {'src': 'fun xs -> List.length xs >= 0'},
                {
                    'src': """\
fun ys ->
   let i = sum ys in
      i >= 0\
"""
                },
            ],
            'instance_reqs': [{'src': 'fun x -> x > 0 && x < 100'}],
            'decomp_reqs': [
                {
                    'name': 'conditional_fn',
                    'basis': [],
                    'rule_specs': [],
                    'prune': True,
                }
            ],
            'opaque_functions': ['helper_function'],
        }
    )


def test_find_nested_recursive_function():
    iml = """\
let f x =
  let rec g y =
    let rec h z =
      z + 1
    in
    h y + 1
  in
  let i w =
    w + 1
  in
g (i x + 1)


let rec normal_rec x =
  if x < 0 then 0 else normal_rec (x - 1)\
"""
    nested_recs = find_nested_rec(iml)

    def pp_nesting(n: Nesting) -> str:
        return (
            f'{unwrap_bytes(n["parent"].function_name.text)} -> '
            f'{unwrap_bytes(n["child"].function_name.text)}'
        )

    assert [pp_nesting(n) for n in nested_recs] == snapshot(
        [
            "b'f' -> b'g'",
            "b'f' -> b'h'",
        ]
    )


def test_update_top_definition():
    """Test update_top_definition with various scenarios.

    - replacement
    - addition by setting keep_previous_definition to True (it's False by
        default)
    - deletion by setting new_definition to empty string
    """
    iml = """\
let f x =
    let rec g y =
    let rec h z =
        z + 1
    in
    h y + 1
    in
    let i w =
    w + 1
    in
g (i x + 1)


let rec normal_rec x =
    if x < 0 then 0 else normal_rec (x - 1)\
"""

    tree = get_parser().parse(bytes(iml, encoding='utf8'))
    iml_2, tree_2 = update_top_definition(
        iml,
        tree,
        top_def_name='f',
        new_definition='let f = x + 1',
    )
    assert iml_2 == snapshot("""\
let f = x + 1


let rec normal_rec x =
    if x < 0 then 0 else normal_rec (x - 1)\
""")

    iml_3, tree_3 = update_top_definition(
        iml_2,
        tree_2,
        top_def_name='normal_rec',
        new_definition='let g = fun x -> x + 1',
    )
    assert iml_3 == snapshot("""\
let f = x + 1


let g = fun x -> x + 1\
""")

    # Add new definition, keep previous definition
    iml_4, tree_4 = update_top_definition(
        iml_3,
        tree_3,
        top_def_name='f',
        new_definition='let f2 = x + 2',
        keep_previous_definition=True,
    )
    assert iml_4 == snapshot("""\
let f = x + 1
let f2 = x + 2

let g = fun x -> x + 1\
""")

    # Delete definition by setting new definition to empty string
    iml_5, tree_5 = update_top_definition(
        iml_4,
        tree_4,
        top_def_name='f',
        new_definition='',
    )
    assert iml_5 == snapshot("""\

let f2 = x + 2

let g = fun x -> x + 1\
""")
    _ = tree_5
