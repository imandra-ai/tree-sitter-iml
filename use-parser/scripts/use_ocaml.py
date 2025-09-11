# pyright: basic
import argparse
import sys
from pathlib import Path

import tree_sitter_ocaml
from rich import print
from tree_sitter import Language, Parser


def print_tree(node, depth=0, max_depth=None):
    """Print the parse tree in a readable format."""
    if max_depth is not None and depth > max_depth:
        return

    indent = '  ' * depth
    if node.children:
        print(f'{indent}{node.type}')
        for child in node.children:
            print_tree(child, depth + 1, max_depth)
    else:
        text = node.text.decode('utf-8') if node.text else ''
        if text.strip():  # Only print non-empty text
            print(f"{indent}{node.type}: '{text}'")
        else:
            print(f'{indent}{node.type}')


def find_errors(node):
    """Recursively find all ERROR nodes in the parse tree."""
    errors = []
    if node.type == 'ERROR':
        errors.append(node)
    for child in node.children:
        errors.extend(find_errors(child))
    return errors


def create_parser(use_iml=False):
    """Create and return an OCaml or IML parser."""
    if use_iml:
        language_capsule = tree_sitter_ocaml.language_iml()
        language = Language(language_capsule)
        print('Successfully loaded local tree-sitter-iml')
    else:
        language_capsule = tree_sitter_ocaml.language_ocaml()
        language = Language(language_capsule)
        print('Successfully loaded local tree-sitter-ocaml')

    parser = Parser()
    parser.language = language
    return parser


def parse_file(file_path, max_depth=None, use_iml=False):
    """Parse a file and display results."""
    file_path = Path(file_path).resolve()

    if not file_path.exists():
        print(f'Error: {file_path} not found')
        return None

    code = file_path.read_text()

    parser = create_parser(use_iml=use_iml)

    # Parse the code
    tree = parser.parse(bytes(code, 'utf-8'))

    print('Parse tree:')
    print_tree(tree.root_node, max_depth=max_depth)

    # Check for errors
    errors = find_errors(tree.root_node)
    if errors:
        print(f'\nFound {len(errors)} parse errors:')
        for i, error in enumerate(errors):
            error_text = error.text.decode('utf-8') if error.text else 'Unknown error'
            # Truncate long error messages
            if len(error_text) > 100:
                error_text = error_text[:100] + '...'
            print(f'  Error {i + 1}: {error_text}')
    else:
        print('\nNo parse errors found!')

    return tree


def main():
    parser = argparse.ArgumentParser(
        description='Parse OCaml/IML files with tree-sitter-ocaml',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        'file',
        nargs='?',
        default='../iml_examples/code-logician-examples/six_swiss.iml',
        help='Path to the OCaml/IML file to parse (default: six_swiss.iml example)',
    )

    parser.add_argument(
        '--max-depth', type=int, help='Maximum depth to display in parse tree'
    )
    
    parser.add_argument(
        '--iml', action='store_true', help='Use IML parser instead of OCaml parser'
    )

    args = parser.parse_args()

    parse_file(
        args.file,
        max_depth=args.max_depth,
        use_iml=args.iml,
    )


if __name__ == '__main__':
    main()
