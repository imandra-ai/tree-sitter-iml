import tree_sitter_ocaml
from tree_sitter import Language, Node, Parser, Tree


def get_language(ocaml: bool = False) -> Language:
    """Get the tree-sitter language for the given language."""
    if ocaml:
        language_capsule = tree_sitter_ocaml.language_ocaml()
    else:
        language_capsule = tree_sitter_ocaml.language_iml()
    return Language(language_capsule)


def get_parser(ocaml: bool = False) -> Parser:
    """Get a parser for the given language."""
    language = get_language(ocaml)

    parser = Parser()
    parser.language = language
    return parser


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
        text = node.text.decode('utf-8') if node.text else ''
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
