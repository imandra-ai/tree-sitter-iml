//! The Topiary IML formatter for JavaScript hosts (browsers, Node, VS Code).
//!
//! Parsing goes through the `web-tree-sitter` JS library, which the host must load and
//! expose as `window.TreeSitter` before calling `init` (the JS wrapper does this).

use std::cell::RefCell;

use js_sys::Uint8Array;
use topiary_core::{formatter_str, Language, Operation, TopiaryQuery};
use wasm_bindgen::prelude::*;

/// The same query file the CLI uses (`imlformat.sh`).
const QUERY: &str = include_str!("../../queries/iml.scm");

thread_local! {
    static LANGUAGE: RefCell<Option<Language>> = const { RefCell::new(None) };
}

/// Initialises web-tree-sitter, loads the IML grammar from `grammar` (the bytes of
/// `tree-sitter-iml.wasm`) and compiles the formatting query. Call once before `format`.
#[wasm_bindgen]
pub async fn init(grammar: Uint8Array) -> Result<(), JsError> {
    topiary_tree_sitter_facade::TreeSitter::init().await?;
    let grammar = topiary_web_tree_sitter_sys::Language::load_bytes(&grammar)
        .await
        .map_err(|e| JsError::new(&format!("failed to load the IML grammar: {e:?}")))?;
    let grammar = topiary_tree_sitter_facade::Language::from(grammar);
    let query = TopiaryQuery::new(&grammar, QUERY).map_err(to_js_error)?;
    let language = Language {
        name: "iml".into(),
        query,
        grammar,
        indent: Some("  ".into()),
    };
    LANGUAGE.with(|cell| cell.replace(Some(language)));
    Ok(())
}

/// Formats IML source. Fails if `init` hasn't run, the input doesn't parse, or formatting
/// isn't idempotent (as the CLI does by default).
#[wasm_bindgen]
pub fn format(input: &str) -> Result<String, JsError> {
    LANGUAGE.with(|cell| {
        let language = cell.borrow();
        let language = language
            .as_ref()
            .ok_or_else(|| JsError::new("imlformat: call init() before format()"))?;
        let mut output = Vec::new();
        let operation = Operation::Format {
            skip_idempotence: false,
            tolerate_parsing_errors: false,
        };
        formatter_str(input, &mut output, language, operation).map_err(to_js_error)?;
        String::from_utf8(output).map_err(|e| JsError::new(&e.to_string()))
    })
}

fn to_js_error(e: topiary_core::FormatterError) -> JsError {
    JsError::new(&e.to_string())
}
