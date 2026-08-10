#!/bin/sh
set -eu

proxy_args=""
if [ "${SOCKS_PROXY:-}" != "" ]; then
  proxy_args="--proxy socks5h://${SOCKS_PROXY}"
fi

ip_url="${IP_URL:-https://api.ipify.org}"
https_url="${HTTPS_URL:-https://www.cloudflare.com/cdn-cgi/trace}"

printf '%s\n' '--- exit IP ---'
# shellcheck disable=SC2086
curl -4 $proxy_args --max-time 15 -fsS "$ip_url"
printf '\n%s\n' '--- HTTPS samples ---'

i=1
while [ "$i" -le 5 ]; do
  # shellcheck disable=SC2086
  curl -4 $proxy_args --max-time 20 -fsS -o /dev/null \
    -w "sample=$i connect=%{time_connect}s tls=%{time_appconnect}s total=%{time_total}s http=%{http_code}\n" \
    "$https_url"
  i=$((i + 1))
done
