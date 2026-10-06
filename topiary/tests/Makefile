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

# Expect tests
# ====================
#
# Each <name>.iml is formatted into <name>.out.iml and compared with <name>.formatted.iml.
# Limit any target to some tests with T, e.g. `make test T=comments_doc` or
# `make diff T='iml_% strings_%'`.

INPUTS := $(filter-out %.formatted.iml %.out.iml,$(wildcard *.iml))
ifdef T
INPUTS := $(filter $(addsuffix .iml,$(T)),$(INPUTS))
endif
OUTS := $(INPUTS:.iml=.out.iml)

# Outputs are regenerated when any of these change.
FORMATTER := ../imlformat.sh ../languages.ncl ../queries/iml.scm \
	$(wildcard ../../grammars/iml/libtree-sitter-iml.*)

# Build every stale output. A test whose formatting fails gets no .out.iml; the error is
# printed and the other tests still run.
GENERATE = $(MAKE) --no-print-directory outputs

.PHONY: test diff promote clean outputs

outputs: $(OUTS)
	@:

%.out.iml: %.iml $(FORMATTER)
	@../imlformat.sh < $< > $@ || { rm -f $@; echo "ERROR $*: formatter failed (see above)"; }

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
	[ $$fail -eq 0 ] || { echo "Run 'make diff' in tests/ to see the changes, 'make promote' to accept them."; exit 1; }

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
	rm -f *.out.iml
