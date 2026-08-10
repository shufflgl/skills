# Server hardening reference

## Identity and files

- Create a dedicated non-login service user and group, for example `proxy`.
- Own runtime configuration and private REALITY material by that user or a root-owned readable group as narrowly required.
- Use directories no broader than `0750`; use secret-bearing files no broader than `0640`, preferably `0600` when the service can read them.
- Keep deployment artifacts, SSH private keys and client credentials out of world-readable paths.

## Privileged ports

Use one deliberate method for port 443:

1. Grant only `CAP_NET_BIND_SERVICE` through systemd capability controls; or
2. Bind an unprivileged port behind a reviewed firewall redirect or reverse proxy.

Do not run the whole daemon as root solely to bind port 443.

## systemd baseline

Set `User=` and `Group=` explicitly. Prefer compatible hardening such as:

- `NoNewPrivileges=true`
- `PrivateTmp=true`
- `ProtectSystem=strict`
- `ProtectHome=true`
- `ProtectKernelTunables=true`
- `ProtectKernelModules=true`
- `ProtectControlGroups=true`
- `RestrictSUIDSGID=true`
- `LockPersonality=true`
- `MemoryDenyWriteExecute=true` only if the selected binary works with it
- `CapabilityBoundingSet=CAP_NET_BIND_SERVICE` and matching ambient capability only when required
- narrow `ReadWritePaths=` for state and logs

Apply hardening incrementally. A permission-denied restart loop is not a reason to discard the low-privilege design; identify the exact file, directory, capability or sandbox denial.

## Firewall and SSH

- Resolve the real SSH port before changing firewall rules.
- Add and verify the proxy port before removing any existing allowance.
- Maintain the provider console as a recovery route.
- Prove a second SSH session after every authentication or firewall change.
- Avoid broad allow rules and unrelated account changes.

## Backup manifest

Record without exposing private values:

- package source and version;
- binary path and checksum;
- config and secret paths;
- systemd unit and drop-ins;
- service user/group identifiers;
- ownership and mode of every required path;
- capabilities;
- firewall rules;
- listener and health-check commands;
- restore order.
