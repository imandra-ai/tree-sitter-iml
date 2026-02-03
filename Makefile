.PHONY: help
help:  ## Show this help message
	@awk '\
		/^# .+$$/ && !/^# [-=]+$$/ { pending=substr($$0, 3); next } \
		/^# =+$$/ && pending { printf "\033[1;33m=== %s ===\033[0m\n", pending; pending=""; next } \
		/^# -+$$/ && pending { printf "\033[1;33m--- %s ---\033[0m\n", pending; pending=""; next } \
		{ pending="" } \
		/^[a-zA-Z_-]+:.*## / { \
			split($$0, a, ":.*## "); \
			printf "\033[36m%-20s\033[0m %s\n", a[1], a[2] \
		}' $(MAKEFILE_LIST)

# Original recipes
# ====================

TS ?= tree-sitter

all install uninstall clean:
	$(MAKE) -C grammars/ocaml $@
	$(MAKE) -C grammars/interface $@
	$(MAKE) -C grammars/type $@

test:
	$(TS) test
	$(SHELL) test/parse-examples.sh

generate:
	cd grammars/ocaml && $(TS) generate
	cd grammars/interface && $(TS) generate
	cd grammars/type && $(TS) generate

# IML specific
# ====================

build-python:  ## Build python package
	rm -rf ./dist/tree_sitter_iml-*
	uv build

publish-python-testpypi:  ## Publish python package to testpypi
	uv publish \
	--index testpypi \
	-u __token__ \
	-p $$(gcloud secrets versions access --project imandra-dev --secret pypi-test-imandrax-api-api-token latest) \
	dist/tree_sitter_iml-*

publish-python-pypi:  ## Publish python package to pypi
	uv publish \
	--index pypi \
	-u __token__ \
	-p $$(gcloud secrets versions access --project imandra-dev --secret pypi-imandrax-api-api-token latest) \
	dist/tree_sitter_iml-*

.PHONY: all install uninstall clean test update generate
