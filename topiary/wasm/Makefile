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

# Build
# ====================
#
# Everything lands in dist/:
# - tree-sitter-iml.wasm: the IML grammar, generated at ABI 14 because web-tree-sitter 0.24
#   (the API the Topiary binding targets) can't load ABI 15.
# - imlformat_wasm{.js,_bg.wasm}: topiary-core plus src/lib.rs, through wasm-bindgen.
#
# The C parts are compiled with the wasi-sdk that `tree-sitter build --wasm` downloads into
# ~/.cache/tree-sitter (tree-sitter >= 0.26), so no emscripten is needed. Override WASM_LLVM
# to use another clang with a wasm32 backend.

TREE_SITTER ?= tree-sitter
WASM_BINDGEN ?= wasm-bindgen
WASM_LLVM ?= $(HOME)/.cache/tree-sitter/wasi-sdk/bin

GRAMMAR := ../../grammars/iml
GRAMMAR_BUILD := target/grammar-abi14
TOPIARY_CORE := target/vendor/topiary-core-0.7.3
RUST_WASM := target/wasm32-unknown-unknown/release/imlformat_wasm.wasm

.PHONY: build grammar formatter test clean

build: grammar formatter  ## build everything into dist/

grammar: dist/tree-sitter-iml.wasm  ## build the IML grammar as wasm

formatter: dist/imlformat_wasm.js  ## build the formatter as wasm

# Regenerated in a copy (same layout, for scanner.c's relative include) so the committed
# ABI 15 parser in grammars/iml/src is left alone.
dist/tree-sitter-iml.wasm: $(GRAMMAR)/grammar.js $(GRAMMAR)/package.json $(GRAMMAR)/src/scanner.c ../../common/scanner.h
	rm -rf $(GRAMMAR_BUILD)
	mkdir -p $(GRAMMAR_BUILD)/grammars/iml/src $(GRAMMAR_BUILD)/common dist
	cp $(GRAMMAR)/grammar.js $(GRAMMAR)/package.json $(GRAMMAR_BUILD)/grammars/iml/
	cp $(GRAMMAR)/src/scanner.c $(GRAMMAR_BUILD)/grammars/iml/src/
	cp ../../common/*.h $(GRAMMAR_BUILD)/common/
	cd $(GRAMMAR_BUILD)/grammars/iml && $(TREE_SITTER) generate --abi 14
	$(TREE_SITTER) build --wasm -o $@ $(GRAMMAR_BUILD)/grammars/iml

# topiary-core 0.7.3 as published doesn't compile for wasm32; patch a copy (see Cargo.toml).
$(TOPIARY_CORE): topiary-core-wasm.patch
	rm -rf $@
	mkdir -p $(dir $@)
	curl -fsSL https://crates.io/api/v1/crates/topiary-core/0.7.3/download | tar xz -C $(dir $@)
	patch -d $@ -p1 < topiary-core-wasm.patch

# cargo tracks the Rust sources itself, so always run it. It needs the grammar built first
# only because that downloads the wasi-sdk.
.PHONY: $(RUST_WASM)
$(RUST_WASM): $(TOPIARY_CORE) dist/tree-sitter-iml.wasm
	CC_wasm32_unknown_unknown=$(WASM_LLVM)/clang AR_wasm32_unknown_unknown=$(WASM_LLVM)/llvm-ar \
	  cargo build --release --target wasm32-unknown-unknown

dist/imlformat_wasm.js: $(RUST_WASM)
	$(WASM_BINDGEN) --target web --out-dir dist $(RUST_WASM)

node_modules: package.json
	npm install
	@touch $@

test: build node_modules  ## format ../tests/*.iml with the wasm build and compare
	node test.mjs

clean:  ## remove build outputs
	rm -rf dist target
