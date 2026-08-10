---
name: deploy-my-private-vps-proxy
category: Workflow
description: Orchestrate my complete private proxy lifecycle from purchasing or receiving a VPS through hardened VLESS REALITY deployment, Apple client setup, safe VPN cutover, performance validation, credential backup, and reusable client artifacts. Use when I ask to build, rebuild, migrate, recover, benchmark, or package my personal VPS proxy setup.
catalog_summary: Build my hardened private VPS proxy and finish with verified Apple clients, performance evidence, and protected reusable backups.
---

# Deploy my private VPS proxy

Turn a fresh VPS into my verified personal proxy while preserving recovery
access, purpose-isolated credentials, low-privilege service operation, and a
repeatable client handoff.

## Dependencies

| Skill | Source | Requirement | Purpose |
| --- | --- | --- | --- |
| `$deploy-private-vps-proxy` | repository | required | Deploy, harden, validate, troubleshoot, benchmark, and package the proxy. |
| `$browser:control-in-app-browser` | Browser plugin | optional | Inspect the provider console and service details when the browser session is available. |
| `$computer-use:computer-use` | Computer Use plugin | optional | Configure and inspect SFM or another macOS client when no purpose-built interface exists. |

## Defaults

- Prefer an existing BandwagonHost Los Angeles VPS; if a purchase is required,
  stop at the final purchase action for approval.
- Prefer Debian, VLESS over TCP, REALITY, `xtls-rprx-vision`, an official Xray
  or sing-box release, and port 443 unless current constraints require another
  design.
- Run the server daemon as a dedicated low-privilege system user. Preserve the
  hardened user, systemd sandbox, ownership, capabilities, and firewall model
  when repairing an existing deployment.
- Use a dedicated Ed25519 SSH key for the VPS and never repurpose an existing
  Git, work, or server key.
- Retrieve and store required secrets through 1Password vault `4AI` using the
  service-account CLI flow. Keep all portable client material in one client
  item when requested, while storing the SSH key separately and excluding the
  server configuration from the client item.
- Prefer SFM on macOS and compatible sing-box clients on iPhone and iPad. Do
  not install GUI applications with Homebrew.
- Prove the node through an isolated local SOCKS inbound before enabling TUN
  or disconnecting a known-good VPN.
- Keep a working recovery connection available until local DNS, HTTPS, exit IP,
  and client logs prove the new path works.
- Finish with separate protected VLESS URI, sing-box JSON, manual parameters,
  and Clash Meta YAML artifacts when reusable files are requested.
- Treat AI/development traffic and US media or Apple TV routing as intended
  workloads, but verify the actual target service rather than assuming an exit
  IP guarantees application compatibility.

An explicit request may override these defaults for one run without weakening
the approval gates or completion criteria.

## Workflow

1. Preflight every dependency. If the required atomic skill is unavailable,
   explain the gap and stop unless I approve a capability-equivalent substitute.
2. Resolve the provider service, region, OS, intended clients, current VPNs,
   1Password access, and recovery route. Pass this inventory to
   `$deploy-private-vps-proxy`.
3. If provider-console interaction is needed and the optional browser skill is
   available, invoke it only to inspect or perform explicitly authorized
   service actions. Hand the verified VPS address and access details back to
   the atomic skill without exposing credentials in chat.
4. Invoke `$deploy-private-vps-proxy` to benchmark the bare VPS, establish and
   verify purpose-isolated SSH access, deploy VLESS REALITY, apply the
   low-privilege service model, configure systemd and firewall boundaries, and
   validate the live server layer by layer.
5. Carry the verified canonical VLESS URI into an isolated localhost SOCKS
   test. Do not proceed to full-device routing until its HTTPS request and exit
   IP succeed.
6. If macOS UI work is required and Computer Use is available, invoke
   `$computer-use:computer-use` to import or update the SFM profile. Pass the
   validated client JSON from the atomic skill and require a full application
   reload after external JSON edits.
7. Use the atomic skill's controlled VPN isolation sequence. Run local tests
   automatically during the cutover and restore the known-good path in reverse
   order if DNS or HTTPS fails.
8. Invoke the atomic skill's validation and benchmark stages. Record actual
   exit IP, DNS result, HTTPS status, repeated timings, returned byte counts,
   download Mbps, upload Mbps, and material limitations.
9. Generate the requested reusable client files with restrictive permissions.
   When 1Password backup is requested, retain the VLESS URI and verified
   sing-box JSON in one client item and verify semantic equality without
   revealing their values.
10. Report the deployed architecture, security posture, active client state,
    measured performance, protected backup locations, recovery path, and any
    deferred Apple TV or router work.

## Approval gates

- Confirm immediately before a purchase, plan change, reinstall, cancellation,
  or other consequential provider action.
- Confirm immediately before changing SSH authentication, firewall access,
  system users, capabilities, systemd security boundaries, or active network
  extensions.
- Confirm immediately before disconnecting a known-good VPN or switching the
  system-wide route; state how connectivity will be restored if the test fails.
- Confirm before saving or transmitting credentials unless the current request
  explicitly names the specific data and 1Password destination.
- Require handoff for any credential-entry step that cannot be completed through
  the authorized 1Password service-account flow.
- Require explicit approval before substituting any required dependency.

## Completion criteria

- Key-only SSH and a provider-console recovery path are both accounted for.
- The proxy daemon is active under the intended low-privilege user, its config
  passes syntax validation, its listener is owned as expected, and its firewall
  exposure is verified.
- An isolated local client reaches HTTPS through the proxy and reports the
  intended server-side exit.
- The final Apple client resolves DNS, reaches HTTPS, reports the intended exit,
  and shows matching outbound traffic in fresh logs.
- Download and upload results include real returned byte counts and explicit
  unit conversion; misleading partial responses are rejected.
- Client credentials are not present in chat, Git, logs, or world-readable
  files.
- Requested portable artifacts pass their relevant syntax checks and use
  restrictive permissions.
- The user receives a tested recovery path and a clear statement of any
  unverified media, Apple TV, router, or multi-VPN behavior.

## Failure handling

- Preserve SSH, provider-console access, the last known-good server config, and
  the last known-good client connection throughout the run.
- Back up live files before mutation. Restore in reverse order when a service
  restart, DNS change, TUN cutover, or firewall change fails.
- If isolated SOCKS fails, stop client TUN work and reconcile the live server
  with the URI. If SOCKS succeeds but TUN fails, keep the server unchanged and
  debug client routing, DNS, and cached configuration.
- If the browser dependency is unavailable, ask the user for the minimum
  non-secret service facts or let them perform the provider-console step; do
  not block server work already reachable over verified SSH.
- If Computer Use is unavailable, provide the validated import artifact and
  exact manual client steps; do not claim the GUI was configured.
- If 1Password CLI, its service-account token, or authorization is unavailable,
  stop secret-dependent work rather than searching plaintext or requesting
  pasted credentials.
- Never weaken the dedicated service user or run the daemon as root merely to
  bypass a permission error. Report the exact ownership, capability, or sandbox
  blocker.
