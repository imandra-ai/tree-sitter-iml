.PHONY: help
help:  ## Show this help (usage: make help)
	@echo "Usage: make [recipe]"
	@echo "Recipes:"
	@awk '/^[a-zA-Z0-9_.-]+:.*?##/ { \
		helpMessage = match($$0, /## (.*)/); \
		if (helpMessage) { \
			recipe = $$1; \
			sub(/:/, "", recipe); \
			printf "  \033[36m%-20s\033[0m %s\n", recipe, substr($$0, RSTART + 3, RLENGTH); \
		} \
	}' $(MAKEFILE_LIST)

# Install
# ====================
#
# Links imlformat.sh onto PATH as `imlformat`, building the grammar library first if needed.
# The link points into this checkout, so keep the repo where it is.

PREFIX ?= $(HOME)/.local
BINDIR := $(PREFIX)/bin
GRAMMAR_SRC := ../grammars/iml/src
ifeq ($(shell uname -s),Darwin)
GRAMMAR_LIB := ../grammars/iml/libtree-sitter-iml.dylib
SHARED_FLAG := -dynamiclib
else
GRAMMAR_LIB := ../grammars/iml/libtree-sitter-iml.so
SHARED_FLAG := -shared
endif

.PHONY: install uninstall grammar

grammar: $(GRAMMAR_LIB)  ## build the IML grammar library that imlformat.sh loads

# Compiled directly rather than via grammars/iml/Makefile, whose common.mak needs GNU make 4
# (macOS ships 3.81). Only the shared library is needed here.
$(GRAMMAR_LIB): $(GRAMMAR_SRC)/parser.c $(GRAMMAR_SRC)/scanner.c
	$(CC) $(SHARED_FLAG) -fPIC -O2 -std=c11 -I$(GRAMMAR_SRC) -I../common $^ -o $@

install: grammar  ## link `imlformat` into $(PREFIX)/bin (default ~/.local/bin)
	@command -v $${TOPIARY:-topiary} >/dev/null || \
	  echo "warning: topiary not found on PATH; install it with 'cargo install topiary-cli --version 0.7.3 --locked'"
	install -d '$(BINDIR)'
	ln -sf '$(CURDIR)/imlformat.sh' '$(BINDIR)/imlformat'
	@echo "Installed $(BINDIR)/imlformat"

uninstall:  ## remove the `imlformat` link
	rm -f '$(BINDIR)/imlformat'

# Tests
# ====================
#
# The snapshot tests and their recipes (diff, promote, clean) live in tests/Makefile.
# `T` is passed through, e.g. `make test T=comments_doc`.

.PHONY: test

test:  ## run the snapshot tests in tests/
	@$(MAKE) --no-print-directory -C tests test
