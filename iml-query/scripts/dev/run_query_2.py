from collections.abc import Generator
from pathlib import Path
from textwrap import indent

import tree_sitter_ocaml
from devtools import pformat, pprint, sprint
from rich import print
from rich.markup import escape
from tree_sitter import Language, Node, Parser, Point, Query, QueryCursor

from iml_query import fmt_node, get_node_lines, get_parser
from iml_query.query import (
    axiom_query,
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
from iml_query.utils import find_pyproject_dir

root_dir = find_pyproject_dir(Path(__file__), 2)


eg_path = root_dir / 'iml_examples' / 'eg.iml'

eg = eg_path.read_text()


parser = get_parser(ocaml=False)
# captures = run_query(verify_query, eg)
# captures = run_query(opaque_query, eg)
# captures = run_query(instance_query, eg)
# captures = run_query(import_query, eg)
captures = run_query(decomp_query, eg)
# captures = run_query(import_query, eg)
# captures = run_query(theorem_query, eg)
# captures = run_query(eval_query, eg)


for query_name, nodes in captures.items():
    print(f'Capture: {query_name}')
    for i, node in enumerate(nodes, 1):
        # print(escape(f'{i}. {fmt_node(node)}'))
        node_s = '\n'.join(get_node_lines(node))
        print(escape(f'{i}.'))
        # print('node:')
        # print(escape(indent(node_s, '  ')))
        if node.text:
            print()
            print('text:')
            print(escape(indent(node.text.decode('utf-8'), '  ')))
        print()
        match node.type:
            case 'verify_statement':
                req = verify_node_to_req(node)
                print('imandrax-api Req:')
                pprint(req)
            case 'instance_statement':
                req = instance_node_to_req(node)
                print('imandrax-api Req:')
                pprint(req)
            case 'eval_statement':
                src = eval_node_to_src(node)
                print('eval src:')
                print(escape(indent(src, '  ')))
            case _:
                pass

        # breakpoint()
