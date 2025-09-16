# pyright: basic
# %%
from collections.abc import Generator
from pathlib import Path
from textwrap import indent

import tree_sitter_ocaml
from devtools import pformat, pprint, sprint
from rich import print
from rich.markup import escape
from tree_sitter import Language, Node, Parser, Point, Query, QueryCursor

from iml_query import fmt_node, get_parser
from iml_query.format import format_treesitter_sexp
from iml_query.query import (
    axiom_query,
    decomp_capture_to_req,
    decomp_query,
    eval_node_to_src,
    eval_query,
    import_query,
    instance_node_to_req,
    instance_query,
    lemma_query,
    mk_query,
    opaque_query,
    run_query,
    theorem_query,
    verify_node_to_req,
    verify_query,
)
from iml_query.tree_sitter_utils import get_node_type_sexpr
from iml_query.utils import find_pyproject_dir

root_dir = find_pyproject_dir(Path(__file__), 2)


def f1(node: Node) -> str:
    return '\n'.join(get_node_type_sexpr(node))


def f2(node: Node) -> str:
    return format_treesitter_sexp(str(node))


Node.__repr__ = lambda self: f2(self)  # ty: ignore[invalid-assignment]


# eg_path = root_dir / 'iml_examples' / 'eg.iml'
eg_path = root_dir / 'iml_examples' / 'decomp_eg3.iml'
eg = eg_path.read_text()


parser = get_parser(ocaml=False)
# matches = run_query(verify_query, eg)
# matches = run_query(opaque_query, eg)
# matches = run_query(instance_query, eg)
# matches = run_query(import_query, eg)
matches = run_query(decomp_query, eg)
# matches = run_query(import_query, eg)
# matches = run_query(theorem_query, eg)
# matches = run_query(eval_query, eg)

# print(matches)
# print('=' * 20)


# %%
payload_node = matches[1][1]['attribute_payload'][0]
expression_item_node = payload_node.children[0]
application_expression_node = expression_item_node.children[0]

# print(payload_node)

print(f1(application_expression_node))
print()
print('=' * 20)
print()
print(f2(application_expression_node))
print()

q = r"""
(application_expression
    (value_path
        (value_name) @top
        (#eq? @top "top")
    )

    (labeled_argument
        (label_name) @assuming
        (extension
            "[%"
            (attribute_id) @attribute_id
            (attribute_payload) @assuming_payload
        )
        (#eq? @assuming "assuming")
        (#eq? @attribute_id "id")
    )?

    (labeled_argument
        (label_name) @basis
        (list_expression
            (extension
                "[%"
                (attribute_id)
                (attribute_payload)
            )+ @basis_extensions
        )

        (#eq? @basis "basis")
    )?

    (labeled_argument
        (label_name) @prune
        (boolean) @prune_value
        (#eq? @prune "prune")
    )?

    (labeled_argument
        (label_name) @ctx_simp
        (boolean) @ctx_simp_value
        (#eq? @ctx_simp "ctx_simp")
    )?

    (labeled_argument
        (label_name) @lift_bool
        (constructor_path
            (constructor_name) @lift_bool_value
        )
        (#eq? @lift_bool "lift_bool")
    )?

    (unit)
)
"""


matches = run_query(query=mk_query(q), node=application_expression_node)

assert len(matches) == 1, f'Expected 1 match, got {len(matches)}'
res = {}
capture = matches[0][1]

print(f'Capture:\n{capture}\n')


class DecompParsingError(Exception):
    pass


if 'assuming' in capture:
    assuming_payload_b = capture['assuming_payload'][0].text
    assert assuming_payload_b, 'Never: no assuming payload'
    assuming_payload = assuming_payload_b.decode('utf-8')
    res['assuming'] = assuming_payload

if 'prune' in capture:
    prune_value_b = capture['prune_value'][0].text
    assert prune_value_b, 'Never: no prune value'
    prune_value: str = prune_value_b.decode('utf-8')
    res['prune'] = prune_value == 'true'

if 'ctx_simp' in capture:
    ctx_simp_value_b = capture['ctx_simp_value'][0].text
    assert ctx_simp_value_b, 'Never: no ctx_simp value'
    ctx_simp_value: str = ctx_simp_value_b.decode('utf-8')
    res['ctx_simp'] = ctx_simp_value == 'true'

if 'lift_bool' in capture:
    lift_bool_value_b = capture['lift_bool_value'][0].text
    assert lift_bool_value_b, 'Never: no lift_bool value'
    lift_bool_value: str = lift_bool_value_b.decode('utf-8')
    lift_bool_enum = ['Default', 'Nested_equalities', 'Equalities', 'All']
    if lift_bool_value not in lift_bool_enum:
        raise DecompParsingError(
            f'Invalid lift_bool value: {lift_bool_value}',
            f'should be one of {lift_bool_enum}',
        )
    res['lift_bool'] = lift_bool_value

print(f'Parsed result:\n{res}\n')

# breakpoint()


# %%
# top_applications: list[Node] = [
#     # no arg
#     get_payload_content(matches, 0)[0],
#     # assume
#     get_payload_content(matches, 1)[0],
#     # basis
#     get_payload_content(matches, 3)[0],
#     # ctx_simp
#     get_payload_content(matches, 4)[0],
# ]

# for app in top_applications:
#     print(node_s(app))
#     print()


# breakpoint()

# assert False

# for i, match in enumerate(matches, 1):
#     print(f'Match {i}')
#     (_, capture) = match
#     capture: dict[str, list[Node]]
#     for query_name, nodes in capture.items():
#         assert len(nodes) == 1, (
#             f'Expected 1 node for {query_name}, got {len(nodes)}'
#         )
#         if query_name in ['func_name', 'attribute_id', 'item_attr']:
#             continue
#         node = nodes[0]
#         print(f'Capture: {query_name = }')

#         # print(escape(f'{i}. {fmt_node(node)}'))
#         node_s = node_to_str(node)
#         # print(escape(indent(node_s, '  ')))

#         if query_name == 'attribute_payload':
#             print(node_s)

#         if node.text:
#             print()
#             print('Node text:')
#             print(escape(indent(node.text.decode('utf-8'), '  ')))
#         print()
#         match query_name, node.type:
#             case _, 'verify_statement':
#                 req = verify_node_to_req(node)
#                 print('imandrax-api Req:')
#                 pprint(req)
#             case _, 'instance_statement':
#                 req = instance_node_to_req(node)
#                 print('imandrax-api Req:')
#                 pprint(req)
#             case _, 'eval_statement':
#                 src = eval_node_to_src(node)
#                 print('eval src:')
#                 print(escape(indent(src, '  ')))
#             case 'decomposed_func', _:
#                 req = decomp_capture_to_req(capture)
#                 print('imandrax-api Req:')
#                 pprint(req)
#             case _:
#                 pass

#             # breakpoint()
#         print('-' * 20)
#     print('=' * 20)
