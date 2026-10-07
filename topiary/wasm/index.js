// The Topiary IML formatter, compiled to WebAssembly. Works in browsers, Node and VS Code
// (desktop and web). See README.md.
import TreeSitter from "web-tree-sitter";

import initModule, { init as loadGrammar, format as formatWasm } from "./dist/imlformat_wasm.js";

let ready;
let loaded = false;

/**
 * Loads web-tree-sitter, the formatter and the IML grammar. Call (and await) once before
 * `format`; later calls return the same promise.
 *
 * @param {object} [options]
 * @param {BufferSource | URL | string} [options.formatterWasm] imlformat_wasm_bg.wasm
 *   (default: next to this file)
 * @param {BufferSource | URL | string} [options.grammarWasm] tree-sitter-iml.wasm
 *   (default: next to this file)
 * @param {object} [options.treeSitter] options for web-tree-sitter's `init`, e.g.
 *   `locateFile` when a bundler moves its tree-sitter.wasm
 */
export function init({ formatterWasm, grammarWasm, treeSitter } = {}) {
  ready ??= (async () => {
    // web-tree-sitter caches its init, so this call's options are the ones used.
    await TreeSitter.init(treeSitter);
    // The Rust binding reads `TreeSitter` off the global object, after checking that the
    // global object is a `Window`. Node and web workers have none, so stand one in.
    if (typeof Window === "undefined") {
      globalThis.Window = class Window {
        static [Symbol.hasInstance](value) {
          return value === globalThis;
        }
      };
    }
    globalThis.TreeSitter = TreeSitter;
    await initModule({
      module_or_path: await load(formatterWasm ?? new URL("./dist/imlformat_wasm_bg.wasm", import.meta.url)),
    });
    await loadGrammar(await load(grammarWasm ?? new URL("./dist/tree-sitter-iml.wasm", import.meta.url)));
    loaded = true;
  })().catch((error) => {
    ready = undefined;
    throw error;
  });
  return ready;
}

/**
 * Formats IML source. Throws if `init` hasn't finished, the input doesn't parse, or the
 * formatting isn't idempotent.
 *
 * @param {string} source
 * @returns {string}
 */
export function format(source) {
  if (!loaded) {
    throw new Error("imlformat: await init() before calling format()");
  }
  return formatWasm(source);
}

// Bytes from a buffer, a file: URL (Node has no fetch for those) or any fetchable URL.
async function load(source) {
  if (ArrayBuffer.isView(source)) {
    return new Uint8Array(source.buffer, source.byteOffset, source.byteLength);
  }
  if (source instanceof ArrayBuffer) {
    return new Uint8Array(source);
  }
  const url = new URL(source, import.meta.url);
  if (url.protocol === "file:") {
    const { readFile } = await import("node:fs/promises");
    return new Uint8Array(await readFile(url));
  }
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`imlformat: failed to fetch ${url}: ${response.status}`);
  }
  return new Uint8Array(await response.arrayBuffer());
}
