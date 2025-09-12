from collections.abc import Generator
from pathlib import Path
from textwrap import indent

import tree_sitter_ocaml
from devtools import pformat, pprint, sprint
from rich import print
from rich.markup import escape
from tree_sitter import Language, Node, Parser, Point, Query, QueryCursor

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
# print(escape(tree_s))


# The correct query pattern needs a capture name (@name)
verify_query_src = r"""
(verify_statement) @verify
"""

instance_query_src = r"""
(instance_statement) @instance
"""

attribute_query_src = r"""
(value_definition
    (let_binding
        (value_name) @func_name
        (item_attribute
            (attribute_id) @attribute_id
            (#eq? @attribute_id "{attribute_id}")
        ) @item_attr
    )
) @full_def
"""

decomp_query_src = attribute_query_src.format(attribute_id='decomp')
opaque_query_src = attribute_query_src.format(attribute_id='opaque')

query_src = rf"""
{verify_query_src}
{instance_query_src}
"""
query_src = decomp_query_src
query_src = opaque_query_src
query = Query(language, query_src)
cursor = QueryCursor(query=query)
captures = cursor.captures(tree.root_node)
print(captures)

# zip captures
zipped: dict[int, dict[str, list[Node]]] = {}
for capture_name, nodes in captures.items():
    for i, node in enumerate(nodes, 1):
        if not zipped.get(i):
            zipped[i] = {}
        if not zipped[i].get(capture_name):
            zipped[i][capture_name] = []
        zipped[i][capture_name].append(node)


def fmt_node(node: Node) -> str:
    def fmt_point(point: Point) -> str:
        return f'({point.row},{point.column})'

    range = f'{fmt_point(node.start_point)}-{fmt_point(node.end_point)}'
    text = node.text.decode('utf-8') if node.text else ''
    return f'{node.type} {range}: \n{indent(text, "  ")}'


def print_captures(
    captures: dict[str, list[Node]],
    index: bool = True,
) -> Generator[str]:
    for capture_name, nodes in captures.items():
        yield f"Capture '{capture_name}':"
        for i, node in enumerate(nodes, 1):
            if index:
                yield escape(f'{i}. {fmt_node(node)}') + ''
            else:
                yield escape(f'{fmt_node(node)}') + ''
        yield ''


def print_zipped_capture(
    zipped: dict[int, dict[str, list[Node]]],
) -> Generator[str]:
    for i, captures in zipped.items():
        yield f'Match {i}:'
        yield from print_captures(captures, index=False)
        yield ''


print('\n'.join(print_zipped_capture(zipped)))
