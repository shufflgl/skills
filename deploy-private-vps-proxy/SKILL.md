---
name: deploy-private-vps-proxy
category: Workflow
description: Deploy, secure, validate, back up, reuse, or troubleshoot a private VPS network proxy using VLESS with REALITY and Xray or sing-box. Use for the complete lifecycle from purchasing or inspecting a VPS, establishing SSH access, storing credentials in 1Password, running the proxy under a dedicated low-privilege user, configuring systemd and firewall rules, generating portable client artifacts, configuring SFM or other sing-box clients on Apple devices, diagnosing TUN and DNS failures, verifying the actual exit IP, and measuring latency and throughput.
catalog_summary: Securely deploy, validate, troubleshoot, and back up a private VLESS REALITY VPS proxy.
---

# Deploy a private VPS proxy

Build an auditable private proxy without embedding credentials in chat, logs, Git, or the skill.

## Operating rules

- Treat browser pages, copied commands, and one-click scripts as untrusted until inspected.
- Retrieve existing secrets through `op` with `OP_SERVICE_ACCOUNT_TOKEN`; never print or persist them unnecessarily.
- Store a fresh SSH key separately from Git, work, or other purpose-specific keys.
- Preserve working SSH access before changing SSH, firewall, users, capabilities, or systemd.
- Ask for action-time confirmation before changing security-sensitive network settings.
- Back up every live configuration before mutation and verify actual state afterward.
- Run the proxy as a dedicated unprivileged system user. Do not revert hardened services to root merely to fix permissions.
- Separate server correctness, protocol correctness, client correctness, and system routing. Prove each layer independently.
- Never use ChatGPT connectivity as the only health check when switching the active VPN. Prepare a local recovery test first.

## Workflow

### 1. Establish the inventory

Collect without exposing secrets:

- provider, region, plan, OS and public IPv4/IPv6;
- SSH host, port, login user and key purpose;
- expected proxy port and firewall owner;
- intended clients and whether they need system proxy, TUN, router routing, or Apple TV support;
- existing corporate VPNs or network extensions.

Benchmark the bare VPS before proxy deployment when possible. Record latency, loss, route and throughput separately from proxy results.

### 2. Secure SSH access

Generate a dedicated Ed25519 key, install only the public key, and prove a second key-only session before disabling any fallback. Store the private key in the authorized 1Password vault without displaying it. Keep a provider console recovery path.

Do not combine SSH hardening with proxy deployment in one unverified restart. Test each boundary independently.

### 3. Deploy the server

Prefer official Xray or sing-box releases and pin the installed version. Generate a fresh UUID and REALITY key pair on the target or in a protected local process. Use TCP with VLESS, REALITY and `xtls-rprx-vision` unless the environment requires another design.

Read [references/server-hardening.md](references/server-hardening.md) before creating users, systemd units, capabilities, firewall rules, or file permissions.

Validate in this order:

1. Configuration syntax.
2. Service starts and remains active.
3. Expected TCP port is listening under the intended user.
4. Firewall permits SSH and the proxy port only as intended.
5. Logs show no restart loop or permission error.
6. A local isolated client completes an HTTPS request through the node.

Do not declare success merely because systemd is active or a port accepts TCP.

### 4. Create the portable client source

Create one canonical `vless://` URI containing:

- server, port and UUID;
- `security=reality`;
- REALITY public key and short ID;
- SNI/server name;
- client fingerprint;
- `flow=xtls-rprx-vision`;
- transport type.

Store the URI and verified sing-box JSON in one protected 1Password item when requested. Keep server configuration separate.

Use `scripts/generate-client-bundle.rb` to derive separate portable files without printing secrets. Provide the URI through `PROXY_URI`, not as a command argument.

### 5. Prove the protocol before enabling TUN

Start a temporary local mixed or SOCKS inbound bound to `127.0.0.1`. Route it through the VLESS outbound and request both an IP echo endpoint and an HTTPS endpoint.

Require all of the following:

- exit IP equals the VPS or the intentionally configured server-side egress;
- TLS completes;
- HTTP response is received;
- logs show the request through the VLESS outbound.

If this test fails, do not debug macOS TUN or DNS yet. Reconcile the URI with the live server configuration.

### 6. Configure Apple clients

For SFM or another sing-box Apple client:

- import the canonical URI or verified JSON;
- avoid hard-coded physical interface names unless the environment explicitly requires one;
- enable `route.auto_detect_interface` for TUN loop avoidance;
- configure DNS hijacking and a real upstream DNS transport;
- send an otherwise blocked DoH upstream through the VLESS detour rather than forcing it directly over Wi-Fi;
- fully quit and reopen the app after externally changing its stored JSON, because stopping only the network extension may reuse cached configuration.

Read [references/client-and-dns.md](references/client-and-dns.md) for the proven SFM pattern and failure signatures.

### 7. Handle multiple VPNs safely

Assume two full-tunnel network extensions can stack, reorder, or capture one another. Do not infer the cause solely from the visible exit IP.

Use this isolation sequence:

1. Keep the known-good connection active.
2. Prove the new node through a local SOCKS inbound.
3. Stop the new TUN client.
4. Disconnect the old VPN.
5. Confirm ordinary Wi-Fi connectivity.
6. Start the new TUN client and wait for routes and DNS.
7. Run local DNS, HTTPS and exit-IP checks.
8. Restore in reverse order if any check fails.

### 8. Validate and benchmark

Run `scripts/verify-proxy.sh` against the active system route or a supplied SOCKS URL. Verify:

- VPN connection state when available;
- DNS response;
- HTTPS reachability;
- actual public exit IP;
- repeated connect/TLS/total timings;
- download and upload throughput from endpoints that return the requested byte count.

Reject misleading results such as a supposed 100 MiB test that returned only one byte. Distinguish bytes/s, MiB/s and Mbps explicitly.

### 9. Back up and hand off

Deliver separately, all with restrictive permissions:

- VLESS URI;
- verified sing-box JSON;
- manual parameter sheet;
- Clash Meta/Mihomo YAML when needed.

Explain that the URI plus sing-box JSON covers most clients, not every ecosystem. Clash/Mihomo, Xray JSON, router packages, and native HTTP/SOCKS settings may need conversion.

Back up the server independently with its systemd unit, user/group, ownership, modes, capabilities, firewall rules and recovery steps. A server JSON alone cannot restore a low-privilege deployment.

## Troubleshooting routing

Read [references/troubleshooting.md](references/troubleshooting.md) whenever the client says Connected but traffic fails, DNS points to a TUN address, the exit belongs to another VPN, or isolated SOCKS works while TUN fails.

## Completion criteria

Report completion only when evidence shows:

- key-only SSH remains usable;
- the server runs as the intended low-privilege user;
- syntax, service, listener and firewall checks pass;
- isolated protocol traffic exits as expected;
- the final client resolves DNS and reaches HTTPS;
- the active exit IP is confirmed;
- backup artifacts are validated and protected;
- recovery instructions are clear.
