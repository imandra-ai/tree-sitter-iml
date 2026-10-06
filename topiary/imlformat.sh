#!/usr/bin/env bash
# Format IML with Topiary, using the IML grammar and queries in this repo.
#
# Usage:
#   ./imlformat.sh file.iml        print the formatted file to stdout
#   ./imlformat.sh < in.iml        read stdin, write stdout
#   ./imlformat.sh -i file.iml ... format files in place
#
# Extra Topiary options can be passed via TOPIARY_ARGS, e.g. TOPIARY_ARGS=-v.
# This script may be symlinked onto PATH (see `make install`).
set -euo pipefail

usage() {
  echo "usage: $(basename "$0") [file.iml]  |  $(basename "$0") -i file.iml ..." >&2
  exit 2
}

# Resolve symlinks so the grammar and queries are found relative to the real script.
src="$0"
while [[ -L "${src}" ]]; do
  dir="$(cd "$(dirname "${src}")" && pwd)"
  src="$(readlink "${src}")"
  [[ "${src}" == /* ]] || src="${dir}/${src}"
done
HERE="$(cd "$(dirname "${src}")" && pwd)"
TOPIARY="${TOPIARY:-topiary}"

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

case "$(uname -s)" in
  Darwin) ext=dylib ;;
  *) ext=so ;;
esac
grammar="${HERE}/../grammars/iml/libtree-sitter-iml.${ext}"
if [[ ! -f "${grammar}" ]]; then
  echo "error: ${grammar} not found; build it with 'cd grammars/iml && gmake'" >&2
  exit 1
fi

# Rewrite the grammar path to an absolute one so this works from any directory.
config="$(mktemp -t topiary-iml.XXXXXX)"
trap 'rm -f "$config"' EXIT
sed "s|\"\\.\\./grammars/iml/libtree-sitter-iml\\.dylib\"|\"${grammar}\"|" "${HERE}/languages.ncl" > "${config}"

export TOPIARY_LANGUAGE_DIR="${HERE}/queries"
# Split TOPIARY_ARGS into words without glob expansion. The ${extra[@]+...} form keeps an
# empty array safe under `set -u` on bash < 4.4 (macOS ships 3.2).
read -r -a extra <<< "${TOPIARY_ARGS:-}"
# No exec: the EXIT trap must still remove $config.
if [[ ${in_place} -eq 1 ]]; then
  "${TOPIARY}" -C "${config}" format ${extra[@]+"${extra[@]}"} "$@"
elif [[ $# -eq 1 ]]; then
  "${TOPIARY}" -C "${config}" format --language iml ${extra[@]+"${extra[@]}"} < "$1"
else
  "${TOPIARY}" -C "${config}" format --language iml ${extra[@]+"${extra[@]}"}
fi
