  1. Source Files Used

  The Python package compiles these C source files directly:
  grammars/ocaml/src/parser.c      ← Generated from grammar.js
  grammars/ocaml/src/scanner.c     ← Custom lexer logic
  grammars/interface/src/parser.c  ← Interface grammar
  grammars/type/src/parser.c       ← Type grammar

  2. Build Process

  grammar.js → [tree-sitter generate] → parser.c + grammar.json + node-types.json
                                     ↓
                           [Python setuptools] → _binding.so (C extension)
                                     ↓
                                tree_sitter_ocaml package

  3. The Generation Flow

  Step 1: Grammar Compilation
  cd grammars/ocaml
  tree-sitter generate  # Creates src/parser.c from grammar.js

  Step 2: Python Extension BuildThe setup.py compiles the generated C files into a Python extension:
  - Input: grammars/ocaml/src/parser.c (the actual parser)
  - Output: _binding.so (Python C extension)
  - Binding: binding.c exposes tree_sitter_ocaml() function to Python

  Step 3: Python Package Assembly
  - tree_sitter_ocaml.language_ocaml() → calls C function → returns PyCapsule
  - PyCapsule contains the actual tree-sitter Language object

  4. Key Insight for IML Extensions

  The parser.c is generated from grammar.js!

  So to add IML support:
  1. ✅ Modify grammars/ocaml/grammar.js (add IML rules)
  2. ✅ Run tree-sitter generate → regenerates parser.c
  3. ✅ Rebuild Python package → gets updated parser automatically
  4. ✅ New IML constructs work in Python immediately

  5. What This Means for Our Implementation

  Our design approach is exactly right:
  - Edit the grammar.js file to add IML rules
  - Generated parser.c will automatically include IML parsing logic
  - Python package rebuild will pick up changes automatically
  - Zero additional C code needed - everything happens in grammar.js

  6. The Build Commands We Need

  # 1. Edit grammar.js to add IML rules
  # 2. Regenerate the parser
  cd grammars/ocaml
  tree-sitter generate

  # 3. Rebuild Python package
  cd ../..
  uv sync  # Rebuilds the local package with new parser.c
