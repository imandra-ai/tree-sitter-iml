#!/usr/bin/env bash
# Format IML with Topiary, using the IML grammar and queries in this repo.
#
# Usage:
#   ./format.sh file.iml ...    format files in place
#   ./format.sh < in.iml        read stdin, write stdout
#
# Extra Topiary options can be passed via TOPIARY_ARGS, e.g. TOPIARY_ARGS=-v.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
TOPIARY="${TOPIARY:-topiary}"

case "$(uname -s)" in
  Darwin) ext=dylib ;;
  *) ext=so ;;
esac
grammar="$HERE/../grammars/iml/libtree-sitter-iml.$ext"
if [[ ! -f "$grammar" ]]; then
  echo "error: $grammar not found; build it with 'cd grammars/iml && gmake'" >&2
  exit 1
fi

# Rewrite the grammar path to an absolute one so this works from any directory.
config="$(mktemp -t topiary-iml.XXXXXX)"
trap 'rm -f "$config"' EXIT
sed "s|\"\\.\\./grammars/iml/libtree-sitter-iml\\.dylib\"|\"$grammar\"|" "$HERE/languages.ncl" > "$config"

export TOPIARY_LANGUAGE_DIR="$HERE/queries"
if [[ $# -eq 0 ]]; then
  exec "$TOPIARY" -C "$config" format --language iml ${TOPIARY_ARGS:-}
else
  exec "$TOPIARY" -C "$config" format ${TOPIARY_ARGS:-} "$@"
fi
