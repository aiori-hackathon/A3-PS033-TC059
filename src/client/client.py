"""Discovery client. MODE=static (no DNS needed) or MODE=dns (signed zone + validating resolver).

Outcomes: VALID, INSECURE, BOGUS, MALFORMED, DIGEST_MISMATCH, UNAVAILABLE, UNAUTHORISED
"""
import hashlib, hmac, json, os, sys
import requests
import dns.flags, dns.resolver, dns.rdatatype, dns.rdtypes.svcbbase as svcb

SERVICES = ["latency", "traceroute", "lossjitter"]
ZONE = os.environ.get("ZONE", "lab.test")
MODE = os.environ.get("MODE", "static")
RESOLVER_IP = os.environ.get("RESOLVER_IP", "127.0.0.1")
RESOLVER_PORT = int(os.environ.get("RESOLVER_PORT", "5301"))
# SVCB private-use key that carries the descriptor's SHA-256 (hex). Must match the zone.
DIGEST_KEY = int(os.environ.get("DIGEST_KEY", "65400"))
TOKEN = os.environ.get("TOKEN")


class Fail(Exception):
    def __init__(self, status, detail):
        self.status, self.detail = status, detail


def discover_static(name):
    with open(os.path.join(os.path.dirname(__file__), "discovery.json")) as f:
        entry = json.load(f).get(name)
    if not entry:
        raise Fail("MALFORMED", f"no entry for {name}")
    return entry["host"], int(entry["port"]), None


def parse_svcb(rdata):
    """Pull host, port and descriptor digest out of one SVCB rdata. Raises Fail(MALFORMED)."""
    try:
        port = rdata.params[svcb.ParamKey.PORT].port
        host = str(rdata.target).rstrip(".")
        hints = rdata.params.get(svcb.ParamKey.IPV4HINT)
        if hints:
            host = str(hints.addresses[0])
    except (KeyError, AttributeError, IndexError, TypeError) as e:
        raise Fail("MALFORMED", f"unusable SVCB record: {e!r}")
    if not (0 < port < 65536) or not host or host == ".":
        raise Fail("MALFORMED", "bad port or target")
    raw = rdata.params.get(DIGEST_KEY)
    if raw is None:
        raise Fail("MALFORMED", f"SVCB record has no descriptor digest (key{DIGEST_KEY})")
    try:
        digest = raw.value.decode("ascii").strip().lower()
    except (AttributeError, UnicodeDecodeError):
        raise Fail("MALFORMED", f"unreadable descriptor digest (key{DIGEST_KEY})")
    if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise Fail("MALFORMED", "descriptor digest is not 64 hex characters")
    return host, port, digest


def discover_dns(name):
    r = dns.resolver.Resolver(configure=False)
    r.nameservers = [RESOLVER_IP]
    r.port = RESOLVER_PORT
    r.use_edns(0, dns.flags.DO, 1232)
    r.lifetime = 5
    fqdn = f"{name}.{ZONE}"
    try:
        ans = r.resolve(fqdn, "SVCB")
    except dns.resolver.NoNameservers as e:
        # Only a real SERVFAIL from the resolver means DNSSEC validation failed.
        if "SERVFAIL" in str(e):
            raise Fail("BOGUS", f"resolver refused {fqdn} (SERVFAIL: DNSSEC validation failed)")
        raise Fail("UNAVAILABLE", f"resolver at {RESOLVER_IP}:{RESOLVER_PORT} unreachable")
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
        raise Fail("MALFORMED", f"no SVCB record for {fqdn}")
    except dns.exception.Timeout:
        raise Fail("UNAVAILABLE", "DNS resolver did not answer")
    if not (ans.response.flags & dns.flags.AD):
        raise Fail("INSECURE", f"{fqdn}: answer not DNSSEC-validated (no AD flag)")
    return parse_svcb(ans[0])


def verify_descriptor(host, port, expected):
    """Fetch the service's descriptor and compare its SHA-256 with the digest from DNS."""
    try:
        resp = requests.get(f"http://{host}:{port}/.well-known/descriptor.json", timeout=3)
    except (requests.ConnectionError, requests.Timeout):
        raise Fail("UNAVAILABLE", f"{host}:{port} not reachable for descriptor")
    if resp.status_code != 200:
        raise Fail("UNAVAILABLE", f"descriptor fetch returned HTTP {resp.status_code}")
    actual = hashlib.sha256(resp.content).hexdigest()
    if not hmac.compare_digest(actual, expected):
        raise Fail("DIGEST_MISMATCH", f"descriptor sha256 {actual[:12]}... != DNS {expected[:12]}...")


def invoke(host, port):
    headers = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}
    try:
        resp = requests.get(f"http://{host}:{port}/probe", headers=headers, timeout=3)
    except (requests.ConnectionError, requests.Timeout):
        raise Fail("UNAVAILABLE", f"{host}:{port} not reachable")
    if resp.status_code in (401, 403):
        raise Fail("UNAUTHORISED", f"service refused ({resp.status_code})")
    if resp.status_code != 200:
        raise Fail("UNAVAILABLE", f"unexpected HTTP {resp.status_code}")
    return resp.json()


def run(name):
    try:
        host, port, digest = discover_static(name) if MODE == "static" else discover_dns(name)
        if digest:  # static mode has no DNS digest to check
            verify_descriptor(host, port, digest)
        return "VALID", invoke(host, port)
    except Fail as f:
        return f.status, f.detail


if __name__ == "__main__":
    print(f"mode={MODE} zone={ZONE}")
    for svc in SERVICES:
        status, detail = run(svc)
        print(f"{svc:<11} {status:<15} {detail}")
