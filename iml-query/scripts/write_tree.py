# pyright: basic
import argparse
from pathlib import Path

import structlog
import tree_sitter_iml
from tree_sitter import Language, Parser

logger = structlog.get_logger()


def print_tree(node, depth=0, max_depth=None):
    """Print the parse tree in a readable format."""
    if max_depth is not None and depth > max_depth:
        return []

    result = []
    indent = '  ' * depth
    if node.children:
        result.append(f'{indent}{node.type}')
        for child in node.children:
            child_result = print_tree(child, depth + 1, max_depth)
            if child_result:  # Only extend if child_result is not empty
                result.extend(child_result)
    else:
        text = node.text.decode('utf-8') if node.text else ''
        if text.strip():  # Only print non-empty text
            result.append(f"{indent}{node.type}: '{text}'")
        else:
            result.append(f'{indent}{node.type}')
    return result


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
        language_capsule = tree_sitter_iml.language_iml()
        language = Language(language_capsule)
    else:
        language_capsule = tree_sitter_iml.language_ocaml()
        language = Language(language_capsule)

    parser = Parser()
    parser.language = language
    return parser


def parse_with_parser(code, use_iml=False, max_depth=None):
    """Parse code and return results."""
    parser = create_parser(use_iml=use_iml)
    tree = parser.parse(bytes(code, 'utf-8'))

    # Get parse tree
    tree_lines = print_tree(tree.root_node, max_depth=max_depth)

    # Check for errors
    errors = find_errors(tree.root_node)
    error_info = []
    if errors:
        for i, error in enumerate(errors):
            error_text = (
                error.text.decode('utf-8') if error.text else 'Unknown error'
            )
            if len(error_text) > 100:
                error_text = error_text[:100] + '...'
            error_info.append(f'Error {i + 1}: {error_text}')

    return {
        'tree': tree_lines,
        'errors': error_info,
        'error_count': len(errors),
    }


def _get_comparison_summary(ocaml_errors, iml_errors):
    """Generate comparison summary between parser results."""
    if ocaml_errors != iml_errors:
        if iml_errors < ocaml_errors:
            return (
                f'✅ IML parser handles this file better '
                f'({iml_errors} vs {ocaml_errors} errors)'
            )
        else:
            return (
                f'⚠️  OCaml parser handles this file better '
                f'({ocaml_errors} vs {iml_errors} errors)'
            )
    else:
        if ocaml_errors == 0:
            return '✅ Both parsers handle this file perfectly'
        else:
            return f'⚠️  Both parsers have {ocaml_errors} errors'


def _write_tree_files(file_path, ocaml_result, iml_result, max_depth):
    """Write separate tree files for each parser."""
    # Create filename suffix with max_depth
    depth_suffix = f'.depth{max_depth}' if max_depth is not None else ''

    # Write OCaml tree
    ocaml_output = (
        file_path.parent / f'{file_path.stem}.ocaml{depth_suffix}.tree'
    )
    with ocaml_output.open('w', encoding='utf-8') as f:
        f.write('\n'.join(ocaml_result['tree']))
        if ocaml_result['errors']:
            f.write('\n\nErrors:\n')
            f.write('\n'.join(ocaml_result['errors']))

    # Write IML tree
    iml_output = file_path.parent / f'{file_path.stem}.iml{depth_suffix}.tree'
    with iml_output.open('w', encoding='utf-8') as f:
        f.write('\n'.join(iml_result['tree']))
        if iml_result['errors']:
            f.write('\n\nErrors:\n')
            f.write('\n'.join(iml_result['errors']))

    logger.info(f'Trees written to: {ocaml_output} and {iml_output}')
    return _get_comparison_summary(
        ocaml_result['error_count'], iml_result['error_count']
    )


def _log_console_results(file_path, ocaml_result, iml_result):
    """Log parsing results to console."""
    header = f'\n{"=" * 80}\nFile: {file_path.name}\n{"=" * 80}\n'
    logger.info(header.strip())
    logger.info('Original file content displayed')

    # Show OCaml parser results
    logger.info(f'OCaml Parser - {ocaml_result["error_count"]} errors')
    for line in ocaml_result['tree']:
        logger.info(line)
    if ocaml_result['errors']:
        logger.info('OCaml Parser Errors:')
        for error in ocaml_result['errors']:
            logger.info(f'  {error}')

    # Show IML parser results
    logger.info(f'IML Parser - {iml_result["error_count"]} errors')
    for line in iml_result['tree']:
        logger.info(line)
    if iml_result['errors']:
        logger.info('IML Parser Errors:')
        for error in iml_result['errors']:
            logger.info(f'  {error}')

    # Summary comparison
    summary = _get_comparison_summary(
        ocaml_result['error_count'], iml_result['error_count']
    )
    logger.info(f'Summary: {summary}')
    return summary


def compare_file_parsing(file_path, max_depth=None, write_files=False):
    """Compare parsing results for a single file."""
    if not file_path.exists():
        logger.error(f'File {file_path} not found')
        return

    code = file_path.read_text()

    # Parse with both parsers
    logger.info(f'Analyzing file: {file_path.name}')
    ocaml_result = parse_with_parser(code, use_iml=False, max_depth=max_depth)
    iml_result = parse_with_parser(code, use_iml=True, max_depth=max_depth)

    # Write results
    if write_files:
        summary = _write_tree_files(
            file_path, ocaml_result, iml_result, max_depth
        )
        logger.info(f'Analysis complete for {file_path.name}: {summary}')
    else:
        _log_console_results(file_path, ocaml_result, iml_result)


def main():
    parser = argparse.ArgumentParser(
        description='Compare OCaml and IML parser outputs for all examples',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        '--examples-dir',
        default='./iml_examples',
        help='Path to the examples directory (default: ../iml_examples)',
    )

    parser.add_argument(
        '--max-depth', type=int, help='Maximum depth to display in parse trees'
    )

    parser.add_argument(
        '--pattern',
        default='*.iml',
        help='File pattern to match (default: *.iml)',
    )

    parser.add_argument(
        '--write-files',
        '-w',
        action='store_true',
        help='Write tree files alongside original files (filename.ocaml.tree, '
        'filename.iml.tree)',
    )

    args = parser.parse_args()

    examples_dir = Path(args.examples_dir).resolve()

    if not examples_dir.exists():
        logger.error(f'Examples directory {examples_dir} not found')
        return

    # Find all matching files
    example_files = list(examples_dir.glob(args.pattern))

    if not example_files:
        logger.error(
            f'No files found matching pattern {args.pattern} in {examples_dir}'
        )
        return

    # Process files
    _process_files(example_files, args.max_depth, args.write_files)


def _process_files(example_files, max_depth, write_files):
    """Process all example files and generate comparison results."""
    summary_msg = f'Found {len(example_files)} files to analyze:'
    logger.info(summary_msg)

    for file in sorted(example_files):
        file_msg = f'  - {file.name}'
        logger.info(file_msg)

    # Compare parsing for each file
    for file_path in sorted(example_files):
        compare_file_parsing(
            file_path, max_depth=max_depth, write_files=write_files
        )

    completion_msg = f'Analysis complete for {len(example_files)} files'
    logger.info(completion_msg)


if __name__ == '__main__':
    main()
