from textwrap import indent

from tree_sitter import Node, Point

from iml_query.tree_sitter_utils import get_language, get_node_lines, get_parser

__all__ = ['get_language', 'get_node_lines', 'get_parser']


def fmt_node(node: Node) -> str:
    def fmt_point(point: Point) -> str:
        return f'({point.row},{point.column})'

    range = f'{fmt_point(node.start_point)}-{fmt_point(node.end_point)}'
    text = node.text.decode('utf-8') if node.text else ''
    return f'{node.type} {range}: \n{indent(text, "  ")}'
