# tree-sitter-iml

This module provides [IML (Imandra Modeling Language)](https://docs.imandra.ai/imandrax/) grammars for the [tree-sitter][] parsing library. It's based on the [tree-sitter-ocaml](https://github.com/tree-sitter/tree-sitter-ocaml) grammar.

## Installation

```sh
pip install tree-sitter-iml
```

You will probably also need the [tree-sitter binding][tree-sitter binding].

```sh
pip install tree-sitter
```

## Usage

Load the grammar as a `Language` object:

```python
import tree_sitter_iml
from tree_sitter import Language, Parser

language_iml = Language(tree_sitter_iml.language_iml())
```

Create a `Parser` and configure it to use the language:

```python
parser = Parser(language_iml)
```

Parse some source code:

```python
tree = parser.parse(iml_code)
```

Use `language_iml()` for IML files, `language_ocaml()` for OCaml files,
`language_ocaml_interface()` to parse interface files (with `.mli` extension),
and `language_ocaml_type()` to parse type signatures.
