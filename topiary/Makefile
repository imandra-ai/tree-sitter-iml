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

# Expect tests
# ====================
#
# Limit any target to some tests with T, e.g. `make test T=comments_doc` or
# `make diff T='iml_% strings_%'`.

TESTS_DIR := tests
INPUTS := $(filter-out %.formatted.iml %.out.iml,$(wildcard $(TESTS_DIR)/*.iml))
ifdef T
INPUTS := $(filter $(addprefix $(TESTS_DIR)/,$(addsuffix .iml,$(T))),$(INPUTS))
endif
OUTS := $(INPUTS:.iml=.out.iml)

# Outputs are regenerated when any of these change.
FORMATTER := imlformat.sh languages.ncl queries/iml.scm \
	$(wildcard ../grammars/iml/libtree-sitter-iml.*)

# Build every stale output. A test whose formatting fails gets no .out.iml; the error is
# printed and the other tests still run.
GENERATE = $(MAKE) --no-print-directory outputs

.PHONY: test diff promote clean outputs

outputs: $(OUTS)
	@:

$(TESTS_DIR)/%.out.iml: $(TESTS_DIR)/%.iml $(FORMATTER)
	@./imlformat.sh < $< > $@ || { rm -f $@; echo "ERROR $*: formatter failed (see above)"; }

# Always reformat from scratch, so a new Topiary binary is picked up too.
test:  ## format every input and compare; expected files are never changed
	@rm -f $(OUTS)
	@$(GENERATE)
	@pass=0; fail=0; \
	for f in $(INPUTS); do n=$${f%.iml}; \
	  if [ ! -f $$n.out.iml ]; then echo "ERROR $$n"; fail=$$((fail + 1)); \
	  elif cmp -s $$n.out.iml $$n.formatted.iml; then pass=$$((pass + 1)); \
	  else echo "FAIL  $$n"; fail=$$((fail + 1)); fi; \
	done; \
	echo "$$pass passed, $$fail failed"; \
	[ $$fail -eq 0 ] || { echo "Run 'make diff' to see the changes, 'make promote' to accept them."; exit 1; }

diff:  ## show the differences as unified diffs (expected -> actual)
	@$(GENERATE)
	@for f in $(INPUTS); do n=$${f%.iml}; \
	  [ -f $$n.out.iml ] && diff -uN $$n.formatted.iml $$n.out.iml; \
	done; true

promote:  ## accept the new output: copy each differing .out.iml over its .formatted.iml
	@$(GENERATE)
	@for f in $(INPUTS); do n=$${f%.iml}; \
	  if [ ! -f $$n.out.iml ]; then echo "skipped $$n: formatter failed"; \
	  elif ! cmp -s $$n.out.iml $$n.formatted.iml; then \
	    cp $$n.out.iml $$n.formatted.iml && echo "updated $$n.formatted.iml"; fi; \
	done

clean:  ## remove the generated .out.iml files
	rm -f $(TESTS_DIR)/*.out.iml
