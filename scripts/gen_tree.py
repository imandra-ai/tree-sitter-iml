#!/usr/bin/env uv run
#
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "tree-sitter",
#     "tree-sitter-iml",
# ]
#
# [tool.uv.sources]
# tree-sitter-iml = { path = "../", editable = true }
# ///

# pyright: basic
"""Generate .tree files from .iml files using tree-sitter-iml parser.

Usage:
    python gen_tree.py <input.iml> [output.tree]
    python gen_tree.py --ocaml <input.iml> [output.tree]

Options:
    --ocaml, -o    Use OCaml parser instead of IML parser (for comparison)

If output is not specified, outputs to:
    <input>.iml.tree   (for IML parser)
    <input>.ocaml.tree (for OCaml parser)

Output Format
-------------
The generated .tree file uses an indented format that shows both field names
and node types for maximum clarity:

    field_name (node_type): 'text'   # for leaf nodes with a field name
    node_type: 'text'                # for leaf nodes without a field name
    field_name (node_type)           # for internal nodes with a field name
    node_type                        # for internal nodes without a field name

Design Rationale:
- Field names show the structural role (how the parent refers to the child)
- Node types show what the node actually is (the grammar rule)
- Showing both helps when debugging grammars or understanding parse trees
- Parenthetical format keeps output compact without extra nesting
- When there's no field name, only the node type is shown

Example output:
    let_binding
      pattern (value_name): 'add_one'
      parameter
        pattern (typed_pattern)
          (: '('
          pattern (value_pattern): 'x'
          :: ':'
          type (type_constructor_path)
            type_constructor: 'int'
          ): ')'
"""

import argparse
import sys
from pathlib import Path

import tree_sitter_iml
from tree_sitter import Language, Parser


def format_tree(
    node, source: bytes, indent: int = 0, field_name: str | None = None
) -> list[str]:
    """Format a tree-sitter node into the custom .tree format.

    Args:
        node: A tree-sitter Node
        source: The source bytes of the parsed file
        indent: Current indentation level
        field_name: The field name from the parent's perspective (if any)

    Returns:
        List of formatted lines
    """
    lines = []
    prefix = "  " * indent

    # Build the label: "field_name (node_type)" or just "node_type"
    if field_name:  # noqa: F841
        label = f"{field_name} ({node.type})"
    else:
        label = node.type

    if node.child_count == 0:
        # Leaf node - show the text
        text = source[node.start_byte : node.end_byte].decode("utf-8")
        # Escape backslashes and single quotes
        text = text.replace("\\", "\\\\").replace("'", "\\'")
        lines.append(f"{prefix}{label}: '{text}'")
    else:
        # Internal node
        lines.append(f"{prefix}{label}")

        # Process children
        for i, child in enumerate(node.children):
            child_field_name = node.field_name_for_child(i)
            child_lines = format_tree(child, source, indent + 1, child_field_name)
            lines.extend(child_lines)

    return lines


def generate_tree(
    input_path: Path, output_path: Path | None = None, use_ocaml: bool = False
) -> None:
    """Generate a .tree file from an .iml file.

    Args:
        input_path: Path to the input .iml file
        output_path: Path to the output .tree file (defaults to input_path + .tree)
        use_ocaml: If True, use OCaml parser instead of IML parser
    """
    if output_path is None:
        if use_ocaml:
            # Replace .iml with .ocaml.tree
            output_path = input_path.with_suffix(".ocaml.tree")
        else:
            output_path = input_path.with_suffix(input_path.suffix + ".tree")

    # Read the source file
    source = input_path.read_bytes()

    # Create parser with selected language
    if use_ocaml:
        language = Language(tree_sitter_iml.language_ocaml())
    else:
        language = Language(tree_sitter_iml.language_iml())
    parser = Parser(language)

    # Parse the source
    tree = parser.parse(source)

    # Format and write the tree
    lines = format_tree(tree.root_node, source)
    output_path.write_text("\n".join(lines) + "\n")

    print(f"Generated: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate .tree files from .iml files using tree-sitter-iml parser.",
        epilog="If output is not specified, outputs to <input>.iml.tree or <input>.ocaml.tree",
    )
    parser.add_argument("input", type=Path, help="Input .iml file")
    parser.add_argument("output", type=Path, nargs="?", help="Output .tree file (optional)")
    parser.add_argument(
        "--ocaml", "-o",
        action="store_true",
        help="Use OCaml parser instead of IML parser (for comparison)",
    )

    args = parser.parse_args()

    if not args.input.exists():
        print(f"Error: File not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    generate_tree(args.input, args.output, args.ocaml)


if __name__ == "__main__":
    main()
