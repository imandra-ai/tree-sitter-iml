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

build-python:
	uv build
	$(MAKE -C iml-query/ build)

publish-python-testpypi:
	uv publish \
	--index testpypi \
	-u __token__ \
	-p $$(gcloud secrets versions access --project imandra-dev --secret pypi-test-imandrax-api-api-token latest)

publish-python-pypi:
	uv publish \
	--index pypi \
	-u __token__ \
	-p $$(gcloud secrets versions access --project imandra-dev --secret pypi-imandrax-api-api-token latest)

.PHONY: all install uninstall clean test update generate
