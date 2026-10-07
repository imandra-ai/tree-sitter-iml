export interface InitOptions {
  /** imlformat_wasm_bg.wasm (default: next to index.js). */
  formatterWasm?: BufferSource | URL | string;
  /** tree-sitter-iml.wasm (default: next to index.js). */
  grammarWasm?: BufferSource | URL | string;
  /** Options for web-tree-sitter's `init`, e.g. `locateFile`. */
  treeSitter?: object;
}

/** Loads web-tree-sitter, the formatter and the IML grammar. Await once before `format`. */
export function init(options?: InitOptions): Promise<void>;

/** Formats IML source. Throws if the input doesn't parse or formatting isn't idempotent. */
export function format(source: string): string;
