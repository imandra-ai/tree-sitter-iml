from collections.abc import Generator
from pathlib import Path
from textwrap import indent

import tree_sitter_ocaml
from devtools import pformat, pprint, sprint
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


# eg_path = root_dir / 'iml_examples' / 'eg.iml'
eg_path = root_dir / 'iml_examples' / 'decomp_eg.iml'

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

print(matches)
print('=' * 20)

# assert False

for i, match in enumerate(matches, 1):
    print(f'Match {i}')
    (_, capture) = match
    capture: dict[str, list[Node]]
    for query_name, nodes in capture.items():
        assert len(nodes) == 1, (
            f'Expected 1 node for {query_name}, got {len(nodes)}'
        )
        if query_name in ['func_name', 'attribute_id', 'item_attr']:
            continue
        node = nodes[0]
        print(f'Capture: {query_name = }')

        # print(escape(f'{i}. {fmt_node(node)}'))
        node_s = '\n'.join(get_node_type_sexpr(node))
        # print(escape(indent(node_s, '  ')))

        if query_name == 'attribute_payload':
            print(node_s)

        if node.text:
            print()
            print('Node text:')
            print(escape(indent(node.text.decode('utf-8'), '  ')))
        print()
        match query_name, node.type:
            case _, 'verify_statement':
                req = verify_node_to_req(node)
                print('imandrax-api Req:')
                pprint(req)
            case _, 'instance_statement':
                req = instance_node_to_req(node)
                print('imandrax-api Req:')
                pprint(req)
            case _, 'eval_statement':
                src = eval_node_to_src(node)
                print('eval src:')
                print(escape(indent(src, '  ')))
            case 'decomposed_func', _:
                req = decomp_capture_to_req(capture)
                print('imandrax-api Req:')
                pprint(req)
            case _:
                pass

            # breakpoint()
        print('-' * 20)
    print('=' * 20)
