# Apple client and DNS reference

## Portable TUN pattern

Use a TUN inbound with a private address, `auto_route: true`, and `strict_route: true`. Use `route.auto_detect_interface: true`. Avoid binding the VLESS outbound to `en0`, `en1`, or another observed interface unless live evidence requires it.

For modern sing-box routing, sniff before matching protocol-dependent rules:

```json
"route": {
  "auto_detect_interface": true,
  "final": "proxy",
  "rules": [
    { "action": "sniff" },
    { "protocol": "dns", "action": "hijack-dns" }
  ]
}
```

Configure a DNS server that can actually be reached from the user's network. If direct Cloudflare DoH is blocked, detour it through the VLESS outbound:

```json
"dns": {
  "servers": [
    {
      "type": "https",
      "tag": "remote-doh",
      "server": "1.1.1.1",
      "server_port": 443,
      "path": "/dns-query",
      "detour": "proxy",
      "tls": {
        "enabled": true,
        "server_name": "cloudflare-dns.com"
      }
    }
  ],
  "final": "remote-doh",
  "strategy": "prefer_ipv4"
}
```

The proxy server address should be an IP when the DNS transport itself detours through that proxy, avoiding a bootstrap dependency.

## SFM persistence behavior

After modifying SFM's stored JSON outside its editor:

1. Stop the profile.
2. Validate the JSON with the matching sing-box version.
3. Fully quit SFM.
4. Reopen SFM.
5. Start the profile.
6. Read fresh logs rather than assuming the disk edit was loaded.

Stopping and starting only the macOS VPN service may reuse an in-memory copy.

## Expected virtual addresses

An address such as `172.19.0.2` may be the TUN's synthetic DNS endpoint. An answer in `198.18.0.0/15` may be a synthetic/fake-IP result. These are not evidence of a malicious LAN DNS server by themselves. Judge success by completed resolution, HTTPS and correct routing.
