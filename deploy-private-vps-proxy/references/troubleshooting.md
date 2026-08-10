# Troubleshooting decision tree

## Connected but no traffic

1. Check whether the app merely reports Connected or actually records outbound traffic.
2. Test the same VLESS parameters through a local SOCKS inbound.
3. If SOCKS fails, compare UUID, port, flow, SNI, REALITY public key, short ID, fingerprint and transport with the live server.
4. If SOCKS succeeds, focus on TUN routes, DNS and client configuration caching.

## Repeated traffic to the TUN DNS address

Log signature:

```text
inbound/tun: connection to 172.x.x.2:53
outbound/vless: connection to 172.x.x.2:53
```

The DNS packet was not hijacked. Add a sniff action before the `protocol: dns` rule, validate, fully reload the application, and read fresh logs.

## DNS hijacked but still times out

Log signature:

```text
dns: exchange failed: dial <physical-interface>: dial tcp 1.1.1.1:443: i/o timeout
```

The DoH transport is attempting direct physical-interface access. Add a detour through the verified proxy outbound or select a demonstrably reachable upstream. Do not change the Mac's global Wi-Fi DNS as a substitute for fixing the client.

## Isolated SOCKS works but TUN exit belongs to another VPN

Inspect which network extension was started first and which application traffic SFM logs show. If SFM proxies the corporate VPN's tunnel endpoints, the chain can become:

```text
application -> corporate VPN -> SFM -> VPS -> corporate VPN exit
```

Use the controlled isolation sequence from SKILL.md. Do not keep toggling the only connection that allows communication with the user.

## External JSON edit appears ignored

Stop and start is insufficient when the GUI cached the profile. Fully quit and reopen the client, then confirm the new behavior in logs.

## SSH accepts TCP then closes

- Read the actual SSH alias, port and user instead of assuming root on port 22.
- Consider a hardened independent user, changed sshd policy, firewall owner, fail2ban, or provider console state.
- Do not weaken the proxy service user or expose secrets to regain access.
- Use the provider console or known-good key path to inspect server logs safely.

## Benchmark sanity

- Confirm the test endpoint returned the requested byte count.
- Convert `bytes/s * 8 / 1,000,000` to Mbps.
- Repeat HTTPS timings; distinguish first connection from reused local connections.
- Treat cross-border latency and throughput as separate results.
