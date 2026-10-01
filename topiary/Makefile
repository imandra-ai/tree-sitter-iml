# Snapshot tests for the Topiary IML formatter.
#
# Each test is a pair of files in tests/: <name>.iml (input) and <name>.formatted.iml
# (expected output). Formatting <name>.iml writes <name>.out.iml, which is compared with
# <name>.formatted.iml.
#
#   make test    format every input and compare; expected files are never changed
#   make diff    show the differences as unified diffs (expected -> actual)
#   make promote accept the new output: copy each differing .out.iml over its .formatted.iml
#   make clean   remove the generated .out.iml files
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
FORMATTER := format.sh languages.ncl queries/iml.scm \
	$(wildcard ../grammars/iml/libtree-sitter-iml.*)

# Build every stale output. A test whose formatting fails gets no .out.iml; the error is
# printed and the other tests still run.
GENERATE = $(MAKE) --no-print-directory outputs

.PHONY: test diff promote clean outputs

outputs: $(OUTS)
	@:

$(TESTS_DIR)/%.out.iml: $(TESTS_DIR)/%.iml $(FORMATTER)
	@./format.sh < $< > $@ || { rm -f $@; echo "ERROR $*: formatter failed (see above)"; }

# Always reformat from scratch, so a new Topiary binary is picked up too.
test:
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

diff:
	@$(GENERATE)
	@for f in $(INPUTS); do n=$${f%.iml}; \
	  [ -f $$n.out.iml ] && diff -uN $$n.formatted.iml $$n.out.iml; \
	done; true

promote:
	@$(GENERATE)
	@for f in $(INPUTS); do n=$${f%.iml}; \
	  if [ ! -f $$n.out.iml ]; then echo "skipped $$n: formatter failed"; \
	  elif ! cmp -s $$n.out.iml $$n.formatted.iml; then \
	    cp $$n.out.iml $$n.formatted.iml && echo "updated $$n.formatted.iml"; fi; \
	done

clean:
	rm -f $(TESTS_DIR)/*.out.iml
