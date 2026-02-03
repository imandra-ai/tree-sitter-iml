PARSER_NAME := iml

# Use npx to run tree-sitter from npm devDependencies since it's not installed globally
TS := npx tree-sitter

# Include ../../common for scanner.h which is shared across grammars
# (common.mak only adds -Isrc by default)
CFLAGS += -I../../common

include ../../common/common.mak

# Regenerate parser from grammar.js (not in common.mak which only rebuilds from grammar.json)
generate:
	$(TS) generate

.PHONY: generate
