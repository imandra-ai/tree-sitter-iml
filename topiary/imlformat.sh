#!/usr/bin/env bash
# Format IML with Topiary, using the IML grammar and queries in this repo.
#
# Usage:
#   ./imlformat.sh [--check | --diff] [PATH ...]
#
#   ./imlformat.sh                   format every *.iml under the current directory in place
#   ./imlformat.sh src/ a.iml        format the given directories and files in place
#   ./imlformat.sh - < in.iml        read stdin, write stdout
#   ./imlformat.sh --check           exit 1 if any file would be reformatted
#   ./imlformat.sh --diff a.iml      print what would change
#
# See imlformat-cli.sh (or --help) for the details. Extra Topiary options can be passed via
# TOPIARY_ARGS, e.g. TOPIARY_ARGS=-v. This script may be symlinked onto PATH (see
# `make install`).
set -euo pipefail

# Resolve symlinks so the grammar and queries are found relative to the real script.
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

TOPIARY="${TOPIARY:-topiary}"
case "$(uname -s)" in
  Darwin) ext=dylib ;;
  *) ext=so ;;
esac
grammar="${HERE}/../grammars/iml/libtree-sitter-iml.${ext}"
if [[ ! -f "${grammar}" ]]; then
  echo "error: ${grammar} not found; build it with 'make grammar' in ${HERE}" >&2
  exit 2
fi

# Rewrite the grammar path to an absolute one so this works from any directory.
config="${WORKDIR}/languages.ncl"
sed "s|\"\\.\\./grammars/iml/libtree-sitter-iml\\.dylib\"|\"${grammar}\"|" "${HERE}/languages.ncl" > "${config}"

export TOPIARY_LANGUAGE_DIR="${HERE}/queries"
# Split TOPIARY_ARGS into words without glob expansion. The ${extra[@]+...} form keeps an
# empty array safe under `set -u` on bash < 4.4 (macOS ships 3.2).
read -r -a extra <<< "${TOPIARY_ARGS:-}"

format_stdin() {
  "${TOPIARY}" -C "${config}" format --language iml ${extra[@]+"${extra[@]}"}
}

run
