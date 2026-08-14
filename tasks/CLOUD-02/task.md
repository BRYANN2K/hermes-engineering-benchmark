# Enforce least-privilege cloud network policy

Implement `validate_stack(stack)` in `solution.py`. It returns a sorted list of violation objects `{"code": CODE, "resource": ID}` and never mutates input. Malformed input raises `ValueError` rather than returning policy violations.

The stack has exactly `networks` and `instances` lists. A network has exactly unique non-empty `id`, `public` (boolean), and `ingress` (list of rules). A rule has exactly `protocol` (`tcp` or `udp`), `port` (integer 1..65535; booleans invalid), and canonical IPv4 CIDR `cidr` (use `ipaddress.ip_network(..., strict=True)`). An instance has exactly unique non-empty `id`, existing `network`, `role` (`web`, `app`, `db`), and `encrypted` boolean.

Policy violations:

- `DB_PUBLIC_NETWORK`: db instance attached to a public network.
- `DB_UNENCRYPTED`: db instance not encrypted.
- `WORLD_ADMIN_PORT`: any network allows world IPv4 (`0.0.0.0/0`) to TCP 22 or 3389.
- `PUBLIC_WEB_MISSING_TLS`: public network containing a web instance lacks an ingress rule for TCP 443 from world IPv4.
- `PRIVATE_WORLD_INGRESS`: a private network has any world IPv4 ingress.
- `UNUSED_PUBLIC_NETWORK`: a public network has no attached instance.

Emit each `(code, resource)` once. Resource is the offending instance for DB codes and the network for all others. Sort by `(resource, code)`. Standard library only. CLI reads one JSON path and prints compact JSON.

Run the visible tests with `python3 -B -m unittest discover -s tests -p 'test_*.py' -v`.
