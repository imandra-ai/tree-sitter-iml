#!/usr/bin/env -S uv run python3
"""Smoke tests for iml-query package."""

import sys
import traceback
from collections.abc import Callable


def test_imports() -> None:
    """Test that all main modules can be imported."""
    print('Testing imports...')

    try:
        import iml_query  # noqa: F401

        print('✓ iml_query imported')
    except ImportError as e:
        raise AssertionError(f'Failed to import iml_query: {e}') from e

    try:
        from iml_query import processing  # noqa: F401

        print('✓ iml_query.processing imported')
    except ImportError as e:
        raise AssertionError(
            f'Failed to import iml_query.processing: {e}'
        ) from e

    try:
        from iml_query import queries  # noqa: F401

        print('✓ iml_query.queries imported')
    except ImportError as e:
        raise AssertionError(f'Failed to import iml_query.queries: {e}') from e

    try:
        from iml_query import tree_sitter_utils  # noqa: F401

        print('✓ iml_query.tree_sitter_utils imported')
    except ImportError as e:
        raise AssertionError(
            f'Failed to import iml_query.tree_sitter_utils: {e}'
        ) from e


def test_tree_sitter_parser() -> None:
    """Test that tree-sitter parser can be created and used."""
    print('Testing tree-sitter parser...')

    from iml_query.tree_sitter_utils import get_parser

    try:
        parser = get_parser()
        print('✓ Parser created successfully')
    except Exception as e:
        raise AssertionError(f'Failed to create parser: {e}') from e

    # Test parsing simple IML code
    test_code = 'let x = 1'
    try:
        tree = parser.parse(bytes(test_code, encoding='utf8'))
        # tree.root_node should never be None for a valid parse
        assert tree.root_node is not None, 'Parser returned None for root_node'
        print('✓ Simple IML code parsed successfully')
    except Exception as e:
        raise AssertionError(f'Failed to parse simple IML code: {e}') from e


def test_query_functionality() -> None:
    """Test basic query functionality."""
    print('Testing query functionality...')

    from iml_query.queries import VERIFY_QUERY_SRC
    from iml_query.tree_sitter_utils import get_parser, mk_query, run_query

    parser = get_parser()

    # Test code with verify statement
    test_code = 'verify (fun x -> x > 0)'
    tree = parser.parse(bytes(test_code, encoding='utf8'))

    try:
        query = mk_query(VERIFY_QUERY_SRC)
        print('✓ Query created successfully')
    except Exception as e:
        raise AssertionError(f'Failed to create query: {e}') from e

    try:
        matches = run_query(query, node=tree.root_node)
        match_list = list(matches)
        if len(match_list) != 1:
            raise AssertionError(f'Expected 1 match, got {len(match_list)}')
        print('✓ Query executed successfully')
    except Exception as e:
        raise AssertionError(f'Failed to run query: {e}') from e


def test_processing_functions() -> None:
    """Test core processing functions."""
    print('Testing processing functions...')

    from iml_query.processing import extract_opaque_function_names, iml_outline

    # Test opaque function extraction
    test_code = """
let func1 x = x + 1
[@@opaque]

let func2 x = x * 2

let func3 y = y - 1
[@@opaque]
"""

    try:
        opaque_funcs = extract_opaque_function_names(test_code)
        expected = ['func1', 'func3']
        if opaque_funcs != expected:
            raise AssertionError(f'Expected {expected}, got {opaque_funcs}')
        print('✓ Opaque function extraction works')
    except Exception as e:
        raise AssertionError(f'Failed to extract opaque functions: {e}') from e

    # Test iml_outline with mixed content
    complex_code = """
let func x = x + 1
[@@opaque]

verify (fun x -> x > 0)

instance (fun y -> y < 10)

let another_func z = z * 2
[@@decomp top ()]
"""

    try:
        outline = iml_outline(complex_code)

        # Verify structure
        if not isinstance(outline, dict):
            raise AssertionError('iml_outline should return a dict')

        expected_keys = {
            'verify_req',
            'instance_req',
            'decompose_req',
            'opaque_function',
        }
        if not expected_keys.issubset(outline.keys()):
            raise AssertionError(
                f'Missing keys in outline: {expected_keys - outline.keys()}'
            )

        # Check some basic content
        if (
            len(outline['opaque_function']) != 1
            or 'func' not in outline['opaque_function'][0]
        ):
            raise AssertionError(
                'Opaque function not correctly extracted in outline'
            )

        if len(outline['verify_req']) != 1:
            raise AssertionError('Verify request not correctly extracted')

        if len(outline['instance_req']) != 1:
            raise AssertionError('Instance request not correctly extracted')

        if len(outline['decompose_req']) != 1:
            raise AssertionError('Decompose request not correctly extracted')

        print('✓ iml_outline works correctly')
    except Exception as e:
        raise AssertionError(f'Failed to create iml outline: {e}') from e


def test_capture_classes() -> None:
    """Test that capture classes work correctly."""
    print('Testing capture classes...')

    from iml_query.queries import VerifyCapture
    from iml_query.tree_sitter_utils import get_parser

    parser = get_parser()

    # Test with simple node creation
    test_code = 'verify (fun x -> x > 0)'
    tree = parser.parse(bytes(test_code, encoding='utf8'))
    root_node = tree.root_node

    # Mock capture dict for testing
    mock_capture = {'verify': [root_node]}

    try:
        verify_capture = VerifyCapture.from_ts_capture(mock_capture)
        if verify_capture.verify != root_node:
            raise AssertionError('VerifyCapture not created correctly')
        print('✓ VerifyCapture works')
    except Exception as e:
        raise AssertionError(f'Failed to create VerifyCapture: {e}') from e


def run_test(test_func: Callable[[], None]) -> tuple[bool, str]:
    """Run a test function and return success status and error message."""
    try:
        test_func()
        return True, ''
    except Exception as e:
        error_msg = f'{e}\n{traceback.format_exc()}'
        return False, error_msg


def main() -> int:
    """Run all smoke tests and return exit code."""
    print('Running iml-query smoke tests...')
    print('=' * 50)

    tests = [
        test_imports,
        test_tree_sitter_parser,
        test_query_functionality,
        test_processing_functions,
        test_capture_classes,
    ]

    passed = 0
    failed = 0

    for test in tests:
        print(f'\n{test.__name__}:')
        success, error = run_test(test)

        if success:
            passed += 1
            print(f'✓ {test.__name__} PASSED')
        else:
            failed += 1
            print(f'✗ {test.__name__} FAILED')
            print(f'Error: {error}')

    print('\n' + '=' * 50)
    print(f'Test Results: {passed} passed, {failed} failed')

    if failed > 0:
        print('❌ Some smoke tests failed!')
        return 1
    else:
        print('✅ All smoke tests passed!')
        return 0


if __name__ == '__main__':
    sys.exit(main())
