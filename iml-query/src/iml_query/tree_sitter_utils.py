from collections import defaultdict
from typing import cast, overload

import structlog
import tree_sitter_iml
from tree_sitter import Language, Node, Parser, Query, QueryCursor, Tree

logger = structlog.get_logger(__name__)


def get_language(ocaml: bool = False) -> Language:
    """Get the tree-sitter language for the given language."""
    if ocaml:
        language_capsule = tree_sitter_iml.language_ocaml()
    else:
        language_capsule = tree_sitter_iml.language_iml()
    return Language(language_capsule)


iml_language = get_language(ocaml=False)


def create_parser(ocaml: bool = False) -> Parser:
    """Get a parser for the given language."""
    language = get_language(ocaml)

    parser = Parser()
    parser.language = language
    return parser


_parser: Parser | None = None


def get_parser() -> Parser:
    global _parser
    if _parser is None:
        _parser = create_parser()
    return _parser


def mk_query(query_src: str) -> Query:
    """Create a Tree-sitter query from the given source."""
    return Query(iml_language, query_src)


def run_query(
    query: Query,
    *,
    code: str | bytes | None = None,
    node: Node | None = None,
) -> list[tuple[int, dict[str, list[Node]]]]:
    """Run a Tree-sitter query on the given code or node.

    Return:
        A list of tuples where the first element is the pattern index and
        the second element is a dictionary that maps capture names to nodes.

    """
    if code is None == node is None:
        raise ValueError('Exactly one of code or node must be provided')

    if code is not None:
        if isinstance(code, str):
            code = bytes(code, 'utf8')

        parser = create_parser(ocaml=False)
        tree = parser.parse(code)

        node = tree.root_node

    node = cast(Node, node)

    cursor = QueryCursor(query=query)
    return cursor.matches(node)


def merge_queries(queries: dict[str, str]) -> str:
    """Merge multiple queries into one query.

    Args:
        queries (dict[str, str]): A dictionary of query names to queries.
            Each query can only contains one pattern.

    Returns:
        str: The merged query.

    """
    s = ''
    for name, query in queries.items():
        if __debug__:
            assert mk_query(query).pattern_count == 1, (
                'expected exactly one pattern'
            )
        s += f'; {name}\n'
        s += query
        s += '\n\n'
    return s


def run_queries(
    queries: dict[str, str],
    node: Node,
) -> dict[str, list[dict[str, list[Node]]]]:
    """Run multiple queries.

    Returns:
    dict[str, list[dict[str, list[Node]]]]: A dictionary of query names to
        a list of captures. Each capture is a dictionary of capture names to
        capture values.

    """
    matches = run_query(
        mk_query(merge_queries(queries)),
        node=node,
    )

    # query name -> list of captures
    captures_map: dict[str, list[dict[str, list[Node]]]] = defaultdict(list)
    query_names = list(queries.keys())
    for patten_idx, capture in matches:
        query_name = query_names[patten_idx]
        captures_map[query_name].append(capture)

    return dict(captures_map)


def unwrap_bytes(node_text: bytes | None) -> bytes:
    if node_text is None:
        raise ValueError('Node text is None')
    return node_text


def get_nesting_relationship(nested_node: Node, top_level_node: Node) -> int:
    """Get nesting relationship between two nodes.

    Returns:
        -1: nested_node is not contained within top_level_node
         0: nested_node is the same as top_level_node
         n > 0: nested_node is nested within top_level_node at level n

    """
    if nested_node == top_level_node:
        return 0

    # Early exit if the nested node is not contained within the top level node
    if (
        nested_node.end_byte < top_level_node.start_byte
        or nested_node.start_byte > top_level_node.end_byte
    ):
        return -1

    level = 0
    current = nested_node.parent

    while current:
        if current == top_level_node:
            return level
        # Count let_expressions as nesting levels
        if current.type == 'let_expression':
            level += 1
        current = current.parent

    return -1  # Range contains but not satisfies let structure


@overload
def delete_nodes(
    iml: str,
    old_tree: Tree,
    *,
    nodes: list[Node],
) -> tuple[str, Tree]: ...


@overload
def delete_nodes(
    iml: str,
    *,
    nodes: list[Node],
) -> tuple[str, None]: ...


def delete_nodes(
    iml: str,
    old_tree: Tree | None = None,
    *,
    nodes: list[Node],
) -> tuple[str, Tree | None]:
    """Delete nodes from IML string and return updated string and tree.

    Return new tree if old_tree is provided.

    Arguments:
        nodes: list of nodes to delete
        iml: old IML code
        old_tree: old parsed tree

    """
    if not nodes:
        return iml, old_tree

    # Extract byte ranges from nodes
    edits = [node.byte_range for node in nodes]

    # Check for overlapping edits
    sorted_edits = sorted(edits, key=lambda x: x[0])
    for i in range(len(sorted_edits) - 1):
        curr_end = sorted_edits[i][1]
        next_start = sorted_edits[i + 1][0]
        if curr_end > next_start:
            raise ValueError(
                f'Overlapping nodes: positions {sorted_edits[i]} and '
                f'{sorted_edits[i + 1]}'
            )

    # Apply deletions to text in reverse order to avoid offset issues
    edits_reversed = sorted(edits, key=lambda x: x[0], reverse=True)
    iml_b = bytes(iml, encoding='utf8')
    for start, end in edits_reversed:
        iml_b = iml_b[:start] + iml_b[end:]
    iml = iml_b.decode('utf8')

    # Get new tree
    # Apply tree edits if we have an old tree
    if old_tree is not None:
        old_tree = old_tree.copy()

        # Sort nodes by start position for tree editing
        sorted_nodes = sorted(nodes, key=lambda x: x.start_byte)

        # Apply tree edits in forward order
        for node in sorted_nodes:
            old_tree.edit(
                start_byte=node.start_byte,
                old_end_byte=node.end_byte,
                new_end_byte=node.start_byte,
                start_point=node.start_point,
                old_end_point=node.end_point,
                new_end_point=node.start_point,
            )

        parser = create_parser(ocaml=False)
        new_tree = parser.parse(iml_b, old_tree=old_tree)
    else:
        new_tree = None

    return iml, new_tree


def insert_lines(
    iml: str,
    tree: Tree,
    lines: list[str],
    insert_after: int,
) -> tuple[str, Tree]:
    r"""Insert lines of code after the given line number.

    AI: this is implemented by AI

    Arguments:
        iml: old IML code
        tree: old parsed tree
        lines: list of lines to insert (without trailing newlines)
        insert_after: line number to insert after
            (0-based, must be < len(lines))

    Returns:
        new IML code and new tree

    Implementation notes:
        Leading newline handling:
            When using splitlines(keepends=True), only the last line may lack
            a trailing newline (if the original string doesn't end with '\n').
            If inserting after such a line, we must prepend '\n' to separate
            the existing line from the inserted content.

        Tree edit point calculation:
            Edit points are (row, col) tuples where col is the byte offset.

            Case 1 - Last line without trailing newline:
                start_point = (insert_after, byte_len_of_line)
                Insertion happens at the end of the current line.

            Case 2 - Normal line with trailing newline:
                start_point = (insert_after + 1, 0)
                Insertion happens at the beginning of the next line.

            For both cases:
                old_end_point = start_point (zero-width insertion)
                new_end_point = (start_row + num_newlines, 0)

    """
    if not lines:
        return iml, tree

    tree = tree.copy()

    # Split into lines to find insertion point
    # TODO: use line info in tree to determine line number
    iml_lines = iml.splitlines(keepends=True)

    # Validate line number
    # Allow insert_after == len(iml_lines) when last line ends with \n
    # (tree.root_node.end_point can point to the line after the last)
    max_insert_after = len(iml_lines) - 1
    if iml_lines and iml_lines[-1].endswith('\n'):
        max_insert_after = len(iml_lines)

    if insert_after < -1 or insert_after > max_insert_after:
        raise ValueError(
            f'Line number {insert_after} out of range (0-{max_insert_after})'
        )

    # Calculate byte position for insertion
    # Find the end of the line we're inserting after
    if insert_after == -1:
        # Inserting at the end of the file
        insert_byte_pos = 0
        need_leading_newline = False
    elif insert_after >= len(iml_lines):
        # Inserting after the last line (when file ends with \n)
        insert_byte_pos = sum(len(line.encode('utf-8')) for line in iml_lines)
        need_leading_newline = False  # Last line already has \n
    else:
        lines_before = iml_lines[: insert_after + 1]
        insert_byte_pos = sum(
            len(line.encode('utf-8')) for line in lines_before
        )
        # Check if we need to add a leading newline
        # (the last line might not end with "\n", so which case we need to add
        # it)
        need_leading_newline = not iml_lines[insert_after].endswith('\n')

    # Prepare the text to insert (ensure lines end with newlines)
    insert_text = '\n'.join(lines)
    if not insert_text.endswith('\n'):
        insert_text += '\n'
    if need_leading_newline:
        insert_text = '\n' + insert_text

    insert_bytes = insert_text.encode('utf-8')
    insert_length = len(insert_bytes)

    # Calculate tree edit points
    if insert_after >= len(iml_lines):
        # Inserting after all lines (file ends with \n)
        start_row = insert_after
        start_col = 0
    elif need_leading_newline:
        # Inserting at the end of line insert_after (no trailing newline)
        start_row = insert_after
        start_col = len(iml_lines[insert_after].encode('utf-8'))
    else:
        # Inserting at the start of the next line
        start_row = insert_after + 1
        start_col = 0

    start_point = (start_row, start_col)
    old_end_point = start_point  # For insertion, old_end = start

    # Calculate end point based on number of newlines inserted
    num_newlines = insert_text.count('\n')
    new_end_point = (start_row + num_newlines, 0)

    # Apply tree edit
    tree.edit(
        start_byte=insert_byte_pos,
        old_end_byte=insert_byte_pos,  # Insertion: old_end = start
        new_end_byte=insert_byte_pos + insert_length,
        start_point=start_point,
        old_end_point=old_end_point,
        new_end_point=new_end_point,
    )

    # Apply text insertion
    iml_bytes = iml.encode('utf-8')
    new_iml_bytes = (
        iml_bytes[:insert_byte_pos] + insert_bytes + iml_bytes[insert_byte_pos:]
    )
    new_iml = new_iml_bytes.decode('utf-8')

    # Parse new tree
    parser = create_parser(ocaml=False)
    new_tree = parser.parse(new_iml_bytes, old_tree=tree)

    return new_iml, new_tree


def fmt_node_with_leaf_text(node: Node) -> str:
    return '\n'.join(get_node_sexpr_with_leaf_text(node))


def fmt_node_with_field_name(node: Node) -> str:
    return get_node_sexpr_with_field_name(str(node))


def get_node_sexpr_with_leaf_text(
    node: Node | Tree,
    depth: int = 0,
    max_depth: int | None = None,
) -> list[str]:
    """Print node type in sexpr format.

    Include 'text' only for leaf nodes.
    """
    if isinstance(node, Tree):
        node = node.root_node

    if max_depth is not None and depth > max_depth:
        return []

    result: list[str] = []
    indent = '  ' * depth
    if node.children:
        result.append(f'{indent}{node.type}')
        for child in node.children:
            child_result = get_node_sexpr_with_leaf_text(
                child, depth + 1, max_depth
            )
            if child_result:  # Only extend if child_result is not empty
                result.extend(child_result)
    else:
        text = unwrap_bytes(node.text).decode('utf-8') if node.text else ''
        if text.strip():  # Only print non-empty text
            result.append(f"{indent}{node.type}: '{text}'")
        else:
            result.append(f'{indent}{node.type}')
    return result


def get_node_sexpr_with_field_name(s_expr: str, indent_size: int = 2):
    """Format tree-sitter S-expression with field names."""
    # Tokenize
    tokens: list[str] = []
    i = 0
    while i < len(s_expr):
        if s_expr[i] in '()':
            tokens.append(s_expr[i])
            i += 1
        elif s_expr[i] == ' ':
            i += 1
        else:
            token = ''
            while i < len(s_expr) and s_expr[i] not in ' ()':
                token += s_expr[i]
                i += 1
            if token:
                tokens.append(token)

    result: list[str] = []
    indent_level = 0
    i = 0

    while i < len(tokens):
        token = tokens[i]

        if token == '(':
            if result and not result[-1].endswith(' '):
                result.append('\n' + ' ' * indent_level)
            result.append('(')

            # Add node type if it exists
            if i + 1 < len(tokens) and tokens[i + 1] not in '()':
                i += 1
                result.append(tokens[i])
                indent_level += indent_size

        elif token == ')':
            indent_level -= indent_size
            result.append(')')

        elif ':' in token:
            # Field name - new line with indentation, but next item stays on
            # same line
            result.append('\n' + ' ' * indent_level + token + ' ')

        else:
            # Regular token
            if result and not result[-1].endswith(' '):
                result.append(' ')
            result.append(token)

        i += 1

    return ''.join(result)


if __name__ == '__main__':
    # Test with your example
    s_expr = """(attribute_payload (expression_item (application_expression function: (value_path (value_name)) argument: (labeled_argument (label_name) expression: (extension (attribute_id) (attribute_payload (expression_item (value_path (value_name)))))) argument: (labeled_argument (label_name) expression: (list_expression (extension (attribute_id) (attribute_payload (expression_item (value_path (value_name))))) (extension (attribute_id) (attribute_payload (expression_item (value_path (value_name))))))) argument: (labeled_argument (label_name) expression: (list_expression (extension (attribute_id) (attribute_payload (expression_item (value_path (value_name))))))) argument: (labeled_argument (label_name) expression: (boolean)) argument: (labeled_argument (label_name) expression: (boolean)) argument: (labeled_argument (label_name) expression: (constructor_path (constructor_name))) argument: (unit))))"""  # noqa: E501

    formatted = get_node_sexpr_with_field_name(s_expr)
    print(formatted)
