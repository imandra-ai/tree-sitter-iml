import tree_sitter_ocaml
from tree_sitter import Language, Node, Parser, Tree
from rich.tree import Tree as RichTree
from rich.markup import escape


def get_parser(ocaml: bool = False) -> Parser:
    """Get a parser for the given language."""
    if ocaml:
        language_capsule = tree_sitter_ocaml.language_ocaml()
    else:
        language_capsule = tree_sitter_ocaml.language_iml()
    language = Language(language_capsule)

    parser = Parser()
    parser.language = language
    return parser


def get_tree_lines(
    node: Node | Tree,
    depth: int = 0,
    max_depth: int | None = None,
) -> list[str]:
    """Print the parse tree in a readable format."""
    if isinstance(node, Tree):
        node = node.root_node

    if max_depth is not None and depth > max_depth:
        return []

    result: list[str] = []
    indent = '  ' * depth
    if node.children:
        result.append(f'{indent}{node.type}')
        for child in node.children:
            child_result = get_tree_lines(child, depth + 1, max_depth)
            if child_result:  # Only extend if child_result is not empty
                result.extend(child_result)
    else:
        text = node.text.decode('utf-8') if node.text else ''
        if text.strip():  # Only print non-empty text
            result.append(f"{indent}{node.type}: '{text}'")
        else:
            result.append(f'{indent}{node.type}')
    return result


def create_rich_tree(node: Node | Tree) -> RichTree:
    """Create a rich.tree.Tree from a tree-sitter Node or Tree."""
    if isinstance(node, Tree):
        node = node.root_node

    def build_tree(node: Node) -> RichTree:
        """Recursively build a rich.tree.Tree."""
        if not node.children:
            text = node.text.decode('utf-8') if node.text else ''
            if text.strip():
                return RichTree(f"{escape(node.type)}: [green]'{escape(text)}'[/green]")
            else:
                return RichTree(escape(node.type))

        tree = RichTree(escape(node.type))
        for child in node.children:
            tree.add(build_tree(child))
        return tree

    return build_tree(node)