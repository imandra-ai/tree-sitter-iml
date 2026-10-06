#!/usr/bin/env bash
# Format IML with the experimental prettier-based formatter from imandrax-vscode
# (imlformat/, VS Code setting `imandrax.IMLFormatter`), for comparison with ./imlformat.sh.
#
# Usage:
#   ./imlformat-prettier.sh file.iml        print the formatted file to stdout
#   ./imlformat-prettier.sh < in.iml        read stdin, write stdout
#   ./imlformat-prettier.sh -i file.iml ... format files in place
#
# Expects the imandrax-vscode repo next to this one, with `npm install` run in it.
# Set IMANDRAX_VSCODE to use a different checkout.
#
# Output and options match the VS Code extension (src/formatter.ts): prettier with
# `semi: false` and the `iml-parse` parser. Like the extension, the output has no trailing
# newline. On a parse or formatter error this prints the error and exits 1, leaving files
# unchanged.
set -euo pipefail

usage() {
  echo "usage: $(basename "$0") [file.iml]  |  $(basename "$0") -i file.iml ..." >&2
  exit 2
}

# Resolve symlinks so the default imandrax-vscode path is relative to the real script.
src="$0"
while [[ -L "${src}" ]]; do
  dir="$(cd "$(dirname "${src}")" && pwd)"
  src="$(readlink "${src}")"
  [[ "${src}" == /* ]] || src="${dir}/${src}"
done
HERE="$(cd "$(dirname "${src}")" && pwd)"

in_place=0
case "${1:-}" in
  -i | --in-place) in_place=1; shift ;;
  -h | --help) usage ;;
  *) ;;
esac
if [[ ${in_place} -eq 1 && $# -eq 0 ]]; then usage; fi
if [[ ${in_place} -eq 0 && $# -gt 1 ]]; then
  echo "error: give one file to print to stdout, or use -i to format several in place" >&2
  exit 2
fi

REPO="${IMANDRAX_VSCODE:-${HERE}/../../imandrax-vscode}"
if [[ ! -f "${REPO}/imlformat/iml-prettier.ts" ]]; then
  echo "error: imandrax-vscode not found at ${REPO}; set IMANDRAX_VSCODE" >&2
  exit 1
fi
REPO="$(cd "${REPO}" && pwd)"
if [[ ! -x "${REPO}/node_modules/.bin/esbuild" || ! -d "${REPO}/node_modules/prettier" ]]; then
  echo "error: run 'npm install' in ${REPO} first" >&2
  exit 1
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
const [plugin_path, ...files] = process.argv.slice(2);
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
    if (files.length === 0) {
      process.stdout.write(await format(fs.readFileSync(0, 'utf8')));
    } else {
      for (const f of files) {
        const out = await format(fs.readFileSync(f, 'utf8'));
        fs.writeFileSync(f, out);
      }
    }
  } catch (e) {
    console.error(`error: ${e.message}`);
    process.exit(1);
  }
})();
EOF

export NODE_PATH="${REPO}/node_modules"
# run.js formats file arguments in place, so only pass them on with -i.
if [[ ${in_place} -eq 1 ]]; then
  exec node "${cache}/run.js" "${cache}/iml-prettier.js" "$@"
elif [[ $# -eq 1 ]]; then
  exec node "${cache}/run.js" "${cache}/iml-prettier.js" < "$1"
else
  exec node "${cache}/run.js" "${cache}/iml-prettier.js"
fi
