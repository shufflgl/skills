#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "usage: $0 <template-file> <output-file> [--force]" >&2
}

redact() {
  sed -E 's/ops_[A-Za-z0-9._=-]+/[REDACTED_OP_SERVICE_ACCOUNT_TOKEN]/g'
}

if [[ $# -lt 2 || $# -gt 3 ]]; then
  usage
  exit 64
fi

template_file="$1"
output_file="$2"
force_flag="${3:-}"

if [[ ! -f "$template_file" ]]; then
  echo "error: template file does not exist: $template_file" >&2
  exit 66
fi

if [[ -e "$output_file" && "$force_flag" != "--force" ]]; then
  echo "error: output file exists; pass --force to overwrite: $output_file" >&2
  exit 73
fi

args=(-i "$template_file" -o "$output_file" --file-mode 0600)
if [[ "$force_flag" == "--force" ]]; then
  args+=(--force)
elif [[ -n "$force_flag" ]]; then
  usage
  exit 64
fi

stderr_file="$(mktemp)"
trap 'rm -f "$stderr_file"' EXIT

if ! op inject "${args[@]}" 2>"$stderr_file"; then
  echo "error: op inject failed" >&2
  redact <"$stderr_file" >&2
  exit 1
fi

chmod 600 "$output_file"
echo "ok: wrote injected secrets to $output_file with mode 0600"
