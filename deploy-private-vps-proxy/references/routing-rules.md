# Portable routing rules

## Model

Keep node credentials separate from routing policy. Maintain domain suffixes and
IP CIDRs once, then generate client-specific fragments with
`scripts/generate-routing-rules.rb`.

Use bypass-mainland ordering:

1. Route the proxy server and private networks directly.
2. Apply personal block, proxy, and direct overrides.
3. Route mainland China domains and IPs directly.
4. Route every unmatched destination through the proxy.

The generator deliberately creates fragments rather than complete client
configurations. Merge each fragment into a validated client configuration so
that client-specific TUN, DNS, node, and outbound settings remain intact.

## Generate

Copy `assets/routing-policy.json` to a protected working directory before
adding personal overrides. Keep the policy free of credentials.

```bash
ruby scripts/generate-routing-rules.rb \
  --policy /protected/path/routing-policy.json \
  --proxy-server VPS_ADDRESS \
  --output /protected/path/generated-rules
```

The output directory contains:

- `sing-box-route.json`: merge its `route` object into SFM or sing-box;
- `v2rayn-xray-routing.json`: import through v2rayN custom routing;
- `mihomo-rules.yaml`: merge its providers and ordered rules into Mihomo;
- `manifest.json`: retain for source and artifact hash verification.

Generate into a new directory. The script refuses to overwrite an artifact.

## Client boundaries

- Use TUN or a transparent router to capture applications that ignore system
  HTTP proxy settings.
- Enable IPv4, IPv6, TCP, UDP, DNS hijacking, and route-aware DNS as supported
  by the selected client.
- Keep platform process rules in local overlays. Windows executable names,
  macOS process paths, iOS applications, and router device policies are not
  portable domain rules.
- Prefer a device-level proxy policy for Apple TV when every application on the
  device must use the US exit. Domain-only Apple media routing is incomplete.
- Preserve the generated proxy-server bypass rule to prevent TUN loops.

## Maintenance

- Review upstream URLs before changing providers. Remote rule sets are trusted
  policy inputs even though they contain no credentials.
- Update personal exceptions first when a domestic domain is missing or an
  overseas domain is misclassified.
- Regenerate all formats together and retain the previous generated directory
  for rollback.
- Validate DNS, HTTPS, exit IP, a domestic site, an AI service, UDP/QUIC, and
  local-network discovery after applying a new rule version.
