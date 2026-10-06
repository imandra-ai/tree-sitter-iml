# shellcheck shell=bash
# Command-line driver shared by imlformat.sh and imlformat-prettier.sh. Source it, call
# `parse_args "$@"`, define `format_stdin` (formats stdin to stdout, exits non-zero on
# error), then call `run`.
#
# Usage: <script> [--check | --diff] [PATH ...]
#
# Formats files in place. A PATH can be a file, a directory (searched recursively for *.iml,
# skipping hidden directories and node_modules), or - for stdin, which is written to stdout.
# With no PATH, formats the current directory.
#
# Exit status: 0 on success, 1 if --check/--diff found files that would be reformatted,
# 2 on a usage error or if any input failed to format.

usage() {
  local name
  name="$(basename "$0")"
  cat <<EOF
usage: ${name} [--check | --diff] [PATH ...]

Format IML files in place. PATH is a file, a directory (searched recursively for *.iml,
skipping hidden directories and node_modules), or - to read stdin and write stdout.
Defaults to the current directory.

options:
  --check     don't write files; exit 1 if any file would be reformatted
  --diff      don't write files; print a unified diff and exit 1 if any file would be
              reformatted
  -h, --help  show this help

Exit status: 0 ok, 1 would reformat (--check/--diff), 2 error.
EOF
}

die_usage() {
  echo "error: $1" >&2
  echo "Run '$(basename "$0") --help' for usage." >&2
  exit 2
}

# Sets MODE (write, check or diff) and PATHS.
parse_args() {
  MODE="write"
  PATHS=()
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --check | --diff)
        [[ ${MODE} == write ]] || die_usage "--check and --diff can't be combined"
        MODE="${1#--}"
        ;;
      -h | --help) usage; exit 0 ;;
      --) shift; PATHS+=("$@"); break ;;
      -) PATHS+=("$1") ;;
      -*) die_usage "unknown option $1" ;;
      *) PATHS+=("$1") ;;
    esac
    shift
  done
  [[ ${#PATHS[@]} -gt 0 ]] || PATHS=(.)
}

# One scratch directory per run, for formatter output and anything format_stdin needs.
WORKDIR="$(mktemp -d "${TMPDIR:-/tmp}/imlformat.XXXXXX")"
trap 'rm -rf "${WORKDIR}"' EXIT

failed=0
changed=0
unchanged=0

# format_one PATH: format a file, or stdin when PATH is -, according to MODE.
format_one() {
  local path="$1" input="$1" out="${WORKDIR}/out"
  if [[ ${path} == - ]]; then
    # Keep a copy of stdin so it can be compared with the output.
    input="${WORKDIR}/stdin"
    cat > "${input}"
  fi
  if ! format_stdin < "${input}" > "${out}"; then
    echo "error: failed to format ${path}" >&2
    failed=$((failed + 1))
    return
  fi
  local same=0
  if cmp -s "${input}" "${out}"; then
    same=1
    unchanged=$((unchanged + 1))
  else
    changed=$((changed + 1))
  fi
  case "${MODE}" in
    write)
      if [[ ${path} == - ]]; then
        cat "${out}"
      elif [[ ${same} -eq 0 ]]; then
        # Overwrite rather than move, so the file keeps its mode and hard links.
        cat "${out}" > "${input}"
        echo "reformatted ${path}" >&2
      fi
      ;;
    check)
      [[ ${same} -eq 1 ]] || echo "would reformat ${path}" >&2
      ;;
    diff)
      # diff exits 1 when the files differ, which is expected here.
      [[ ${same} -eq 1 ]] || diff -u -L "${path}" -L "${path}" "${input}" "${out}" || true
      ;;
    *) ;;
  esac
}

run() {
  local path file
  for path in "${PATHS[@]}"; do
    if [[ ${path} == - ]]; then
      format_one -
    elif [[ -d ${path} ]]; then
      # -mindepth 1 so a starting directory like . isn't pruned as hidden.
      while IFS= read -r file; do
        format_one "${file}"
      done < <(find "${path}" -mindepth 1 -type d \( -name '.*' -o -name node_modules \) -prune \
        -o -type f -name '*.iml' -print | LC_ALL=C sort)
    elif [[ -f ${path} ]]; then
      format_one "${path}"
    else
      echo "error: ${path}: no such file or directory" >&2
      failed=$((failed + 1))
    fi
  done

  # Summary on stderr, so stdout only carries formatted stdin or diffs.
  local verb=reformatted
  [[ ${MODE} == write ]] || verb="would be reformatted"
  if [[ ${PATHS[*]} != - ]]; then
    echo "${changed} file(s) ${verb}, ${unchanged} unchanged, ${failed} failed" >&2
  fi

  if [[ ${failed} -gt 0 ]]; then exit 2; fi
  if [[ ${MODE} != write && ${changed} -gt 0 ]]; then exit 1; fi
  exit 0
}
