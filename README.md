# tree-sitter-iml

- Goal
    - extract verify / instance / decompose requests that can be consumed by [imandrax-api](https://github.com/imandra-ai/imandrax-api) from IML files.
    - IML code manipulation: eg change IML code given `imandrax-api` requests
- Cloned from [tree-sitter-ocaml](https://github.com/tree-sitter/tree-sitter-ocaml) with additional grammar for IML-specific structures. It should be compatible with regular OCaml code.
- There's a Python API `iml-query/`
