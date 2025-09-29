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
