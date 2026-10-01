# Topiary configuration for IML.
#
# Topiary v0.7.x resolves relative paths against the current directory, so this file
# works as-is only when Topiary is run from this folder. ./format.sh handles that for you.
{
  languages = {
    iml = {
      extensions = ["iml"],
      indent = "  ",
      grammar.source.path = "../grammars/iml/libtree-sitter-iml.dylib",
    },
  },
}
