from tree_sitter import Node

from iml_query.tree_sitter_utils import get_node_type_sexpr


def f1(node: Node) -> str:
    return '\n'.join(get_node_type_sexpr(node))


def f2(node: Node) -> str:
    return format_treesitter_sexp(str(node))


def format_treesitter_sexp(s_expr: str, indent_size: int = 2):
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
            # Field name - new line with indentation, but next item stays on same line
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

    formatted = format_treesitter_sexp(s_expr)
    print(formatted)
