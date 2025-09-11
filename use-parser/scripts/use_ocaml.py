# pyright: basic
import sys
from pathlib import Path

from tree_sitter import Language, Parser


def print_tree(node, depth=0):
    """Print the parse tree in a readable format."""
    indent = '  ' * depth
    if node.children:
        print(f'{indent}{node.type}')
        for child in node.children:
            print_tree(child, depth + 1)
    else:
        text = node.text.decode('utf-8') if node.text else ''
        if text.strip():  # Only print non-empty text
            print(f"{indent}{node.type}: '{text}'")
        else:
            print(f'{indent}{node.type}')


def test_ocaml_parser():
    # Use the local tree-sitter-ocaml package
    try:
        import tree_sitter_ocaml

        ocaml_language_capsule = tree_sitter_ocaml.language_ocaml()
        ocaml_language = Language(ocaml_language_capsule)
        print('Successfully loaded local tree-sitter-ocaml')
    except ImportError as e:
        print(f'Error importing tree_sitter_ocaml: {e}')
        print("Make sure to run 'uv sync' to install the local package")
        return

    # Create parser
    parser = Parser()
    parser.language = ocaml_language

    # Test with an IML example that has verification keywords
    iml_file = Path('../iml_examples/imandrax-examples/ackermann.iml').resolve()

    if not iml_file.exists():
        print(f'Error: {iml_file} not found')
        return

    with open(iml_file) as f:
        code = f.read()

    print(f'Parsing {iml_file.name}...')
    print('=' * 50)
    print(code[:200] + '...' if len(code) > 200 else code)
    print('=' * 50)

    # Parse the code
    tree = parser.parse(bytes(code, 'utf-8'))

    print('Parse tree:')
    print_tree(tree.root_node)

    # Check for errors
    def find_errors(node):
        errors = []
        if node.type == 'ERROR':
            errors.append(node)
        for child in node.children:
            errors.extend(find_errors(child))
        return errors

    errors = find_errors(tree.root_node)
    if errors:
        print(f'\nFound {len(errors)} parse errors:')
        for i, error in enumerate(errors):
            print(
                f'  Error {i + 1}: {error.text.decode("utf-8") if error.text else "Unknown error"}'
            )
    else:
        print('\nNo parse errors found!')


if __name__ == '__main__':
    test_ocaml_parser()
