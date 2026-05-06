#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "usage: $0 'op://vault/item/field'" >&2
}

redact() {
  sed -E 's/ops_[A-Za-z0-9._=-]+/[REDACTED_OP_SERVICE_ACCOUNT_TOKEN]/g'
}

if [[ $# -ne 1 ]]; then
  usage
  exit 64
fi

ref="$1"
if [[ "$ref" != op://* ]]; then
  echo "error: expected an op:// secret reference" >&2
  usage
  exit 64
fi

stderr_file="$(mktemp)"
trap 'rm -f "$stderr_file"' EXIT

if ! op read "$ref" 2>"$stderr_file"; then
  echo "error: op read failed for the provided secret reference" >&2
  redact <"$stderr_file" >&2
  exit 1
fi
