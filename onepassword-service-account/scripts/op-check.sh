#!/usr/bin/env bash
set -euo pipefail

redact() {
  sed -E 's/ops_[A-Za-z0-9._=-]+/[REDACTED_OP_SERVICE_ACCOUNT_TOKEN]/g'
}

if ! command -v op >/dev/null 2>&1; then
  echo "error: 1Password CLI 'op' was not found on PATH" >&2
  exit 127
fi

if [[ -z "${OP_SERVICE_ACCOUNT_TOKEN:-}" ]]; then
  echo "error: OP_SERVICE_ACCOUNT_TOKEN is not set" >&2
  exit 2
fi

if [[ "${1:-}" == "--no-network" ]]; then
  echo "ok: op $(op --version) is installed and OP_SERVICE_ACCOUNT_TOKEN is set"
  exit 0
fi

stdout_file="$(mktemp)"
stderr_file="$(mktemp)"
trap 'rm -f "$stdout_file" "$stderr_file"' EXIT

if op vault list --format json >"$stdout_file" 2>"$stderr_file"; then
  echo "ok: op $(op --version) can authenticate with the service account"
  exit 0
fi

echo "error: op could not authenticate or list accessible vaults" >&2
redact <"$stderr_file" >&2
exit 1
