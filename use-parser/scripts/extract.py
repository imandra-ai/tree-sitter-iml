from pathlib import Path

import tree_sitter_ocaml
from devtools import pformat, pprint, sprint
from rich import print
from rich.markup import escape
from tree_sitter import Language, Parser, Query, QueryCursor

from use_parser import get_parser, get_tree_lines
from use_parser.utils import find_pyproject_dir

root_dir = find_pyproject_dir(Path(__file__), 2)


eg_path = root_dir / 'iml_examples' / 'eg.iml'

eg = eg_path.read_text()

parser = get_parser(ocaml=False)
language = parser.language
assert language

tree = parser.parse(bytes(eg, 'utf-8'))

# print(tree.root_node.children[-1].text)

tree_s = '\n'.join(get_tree_lines(tree))


verify_query_src = r'(verify_statement)'
verify_query = Query(
    language,
    verify_query_src,
)

out = QueryCursor(
    query=verify_query,
).captures(
    tree.root_node,
)

print(out)

# print(escape(tree_s))
