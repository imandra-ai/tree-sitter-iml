# pyright: basic
# %%
from collections.abc import Generator
from pathlib import Path
from textwrap import indent

import tree_sitter_ocaml
from devtools import pformat, pprint, sprint
from iml_query.format import format_treesitter_sexp
from rich import print
from rich.markup import escape
from tree_sitter import Language, Node, Parser, Point, Query, QueryCursor

from iml_query import fmt_node, get_parser
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

matches = run_query(
    query=extract_top_arg_query, node=application_expression_node
)
print(f'Found {len(matches)} labeled arguments')

print(f'Matches: \n{matches}')

res = {}


class DecompParsingError(Exception):
    pass


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
            assuming_matches = run_query(query=assuming_query, node=arg_node)
            if assuming_matches:
                payload_text = assuming_matches[0][1]['payload'][0].text
                assert payload_text, 'Never: no assuming payload'
                res['assuming'] = payload_text.decode('utf-8')

        case 'basis' | 'rule_specs':
            # Parse list of identifiers: ~basis:[[%id simple_branch] ; [%id f]]
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
            extension_matches = run_query(query=extension_query, node=arg_node)
            if extension_matches:
                ids = []
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
                assert constructor_text, 'Never: no lift_bool constructor text'
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
