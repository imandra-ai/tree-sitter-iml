.PHONY: write-example-trees
write-example-trees:
	uv run scripts/write_tree.py --examples-dir ../iml_examples --write-files

.PHONY: cicd-format
cicd-format:
	uvx ruff format . --check

.PHONY: cicd-lint
cicd-lint:
	uvx ruff check . --no-fix --output-format=github

.PHONY: cicd-type-check
cicd-type-check:
	uvx pyright src/ tests/

.PHONY: test
test:
	uv run pytest -vvv

.PHONY: build
	(cd .. && uv build)

.PHONY: test-wheel
test-wheel:
	uv run --isolated --no-project --with ../dist/iml_query-*.whl --with ../dist/tree_sitter_iml-*.whl tests/smoke_test.py

.PHONY: test-source-dist
test-source-dist:
	cd .. && uv build
	uv run --isolated --no-project --with ../dist/iml_query-*.tar.gz --with ../dist/tree_sitter_iml-*.tar.gz tests/smoke_test.py
