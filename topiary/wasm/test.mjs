// Runs the snapshot tests in ../tests through the wasm formatter: each <name>.iml must format
// to <name>.formatted.iml, as with the CLI (`make test` in ../tests). Without NAMEs, also
// checks the known differences from the native formatter.
//
// Usage: node test.mjs [NAME ...]
import { readdir, readFile } from "node:fs/promises";

import { format, init } from "./index.js";

const dir = new URL("../tests/", import.meta.url);
const only = process.argv.slice(2);
const names = (await readdir(dir))
  .filter((f) => f.endsWith(".iml") && !/\.(formatted|out)\.iml$/.test(f))
  .map((f) => f.slice(0, -".iml".length))
  .filter((n) => only.length === 0 || only.includes(n))
  .sort();

await init();

let pass = 0;
let fail = 0;
for (const name of names) {
  const input = await readFile(new URL(`${name}.iml`, dir), "utf8");
  const expected = await readFile(new URL(`${name}.formatted.iml`, dir), "utf8");
  let actual;
  try {
    actual = format(input);
  } catch (error) {
    console.log(`ERROR ${name}: ${error.message}`);
    fail++;
    continue;
  }
  if (actual === expected) {
    pass++;
  } else {
    console.log(`FAIL  ${name}`);
    fail++;
  }
}

// Known difference from the native formatter: the wasm grammar is built at ABI 14, which
// drops `reserved` words, so IML keywords are accepted as identifiers and this invalid IML is
// formatted instead of rejected (see README.md). If one of these starts failing to parse, the
// workaround is gone: delete this list and the README section.
const keywordsAsIdentifiers = [
  "let theorem = 1\n",
  "let x = test\n",
  "type t = { verify : int }\n",
  "let x = r.lemma\n",
  "let x = A.instance\n",
];
if (only.length === 0) {
  for (const input of keywordsAsIdentifiers) {
    const name = `keyword leniency: ${JSON.stringify(input.trim())}`;
    try {
      format(input);
      pass++;
    } catch {
      console.log(`FAIL  ${name} is now rejected; update test.mjs and README.md`);
      fail++;
    }
  }
}

console.log(`${pass} passed, ${fail} failed`);
process.exitCode = fail === 0 ? 0 : 1;
