#!/usr/bin/env bash
# Format IML with the experimental prettier-based formatter from imandrax-vscode
# (imlformat/, VS Code setting `imandrax.IMLFormatter`), for comparison with ./imlformat.sh.
#
# Usage: ./imlformat-prettier.sh [--check | --diff] [PATH ...]
#
# Same command line as ./imlformat.sh: formats files and directories in place, - for stdin.
# See imlformat-cli.sh (or --help) for the details.
#
# Expects the imandrax-vscode repo next to this one, with `npm install` run in it.
# Set IMANDRAX_VSCODE to use a different checkout.
#
# Output and options match the VS Code extension (src/formatter.ts): prettier with
# `semi: false` and the `iml-parse` parser. Like the extension, the output has no trailing
# newline, so files with one count as reformatted. A file that fails to parse is reported
# and left unchanged.
set -euo pipefail

# Resolve symlinks so the default imandrax-vscode path is relative to the real script.
src="$0"
while [[ -L "${src}" ]]; do
  dir="$(cd "$(dirname "${src}")" && pwd)"
  src="$(readlink "${src}")"
  [[ "${src}" == /* ]] || src="${dir}/${src}"
done
HERE="$(cd "$(dirname "${src}")" && pwd)"

# shellcheck source=imlformat-cli.sh
source "${HERE}/imlformat-cli.sh"
parse_args "$@"

REPO="${IMANDRAX_VSCODE:-${HERE}/../../imandrax-vscode}"
if [[ ! -f "${REPO}/imlformat/iml-prettier.ts" ]]; then
  echo "error: imandrax-vscode not found at ${REPO}; set IMANDRAX_VSCODE" >&2
  exit 2
fi
REPO="$(cd "${REPO}" && pwd)"
if [[ ! -x "${REPO}/node_modules/.bin/esbuild" || ! -d "${REPO}/node_modules/prettier" ]]; then
  echo "error: run 'npm install' in ${REPO} first" >&2
  exit 2
fi

# Bundle the plugin once per version of its sources, outside both repos.
hash="$(cat "${REPO}"/imlformat/*.ts "${REPO}/imlformat/iml2json.bc.js" | shasum | cut -c1-12)"
cache="${TMPDIR:-/tmp}/imlformat-prettier-${hash}"
if [[ ! -f "${cache}/iml-prettier.js" ]]; then
  mkdir -p "${cache}"
  "${REPO}/node_modules/.bin/esbuild" "${REPO}/imlformat/iml-prettier.ts" --bundle \
    --outfile="${cache}/iml-prettier.js.tmp" --format=cjs --platform=node \
    --external:prettier --log-level=warning
  mv "${cache}/iml-prettier.js.tmp" "${cache}/iml-prettier.js"
fi

# The runner is a file, not `node -` with a heredoc, so stdin stays free for the IML input.
cat > "${cache}/run.js" <<'EOF'
const fs = require('fs');
const prettier = require('prettier');
const plugin_path = process.argv[2];
const plugin = require(plugin_path);

async function format(text) {
  // The bundled parser reports syntax errors with console.log; keep them off stdout.
  const log = console.log;
  console.log = (...args) => console.error(...args);
  try {
    return await prettier.format(text, { semi: false, parser: 'iml-parse', plugins: [plugin] });
  } finally {
    console.log = log;
  }
}

(async () => {
  try {
    process.stdout.write(await format(fs.readFileSync(0, 'utf8')));
  } catch (e) {
    console.error(`error: ${e.message}`);
    process.exit(1);
  }
})();
EOF

export NODE_PATH="${REPO}/node_modules"
format_stdin() {
  node "${cache}/run.js" "${cache}/iml-prettier.js"
}

run
