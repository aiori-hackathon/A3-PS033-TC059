"""Scripted test cases for the discovery client.

Run from src/client with the mock services up (docker compose up -d in src) and TOKEN set:
    py test_cases.py            # offline-capable cases (needs only the services on 8081-8083)
    py test_cases.py --live     # also runs the full DNS discovery once A's zone has the digests

Each case reports the status the client assigns, and PASS/FAIL against what we expect.
"""
import os, sys
import dns.rdata, dns.rdataclass, dns.rdatatype, dns.resolver
import client

GOOD = "f9ae09f2df370aa461cf6ca43410af79fdef6b95c36fc62871d6be1b6b54d250"
REAL_TOKEN = os.environ.get("TOKEN", "")
client.TOKEN = REAL_TOKEN


def status_of(fn):
    """Run fn; return the client's status string for what happened."""
    try:
        fn()
        return "VALID"
    except client.Fail as f:
        return f.status
    except Exception as e:  # a crash is a test failure, not a classification
        return f"CRASH:{type(e).__name__}"


def svcb(text):
    return dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.SVCB, text)


def case_valid():
    client.TOKEN = REAL_TOKEN
    return status_of(lambda: client.invoke("127.0.0.1", 8081))


def case_unauthorised():
    client.TOKEN = "definitely-wrong-token"
    try:
        return status_of(lambda: client.invoke("127.0.0.1", 8081))
    finally:
        client.TOKEN = REAL_TOKEN


def case_unavailable_service():
    return status_of(lambda: client.invoke("127.0.0.1", 9))  # nothing listens on port 9


def case_digest_mismatch():
    return status_of(lambda: client.verify_descriptor("127.0.0.1", 8081, "0" * 64))


def case_malformed():
    bad = [
        f"1 . ipv4hint=127.0.0.1 key65400={GOOD}",          # no port
        "1 . port=8081 ipv4hint=127.0.0.1",                 # no digest
        "1 . port=8081 ipv4hint=127.0.0.1 key65400=abc123",  # digest too short
    ]
    results = {status_of(lambda t=t: client.parse_svcb(svcb(t))) for t in bad}
    return results.pop() if len(results) == 1 else "MIXED:" + ",".join(sorted(results))


def case_bogus():
    """Resolver answers SERVFAIL (what a validating resolver does for bad DNSSEC data)."""
    class FakeServfail(dns.resolver.NoNameservers):
        def __str__(self):
            return "All nameservers failed: Server Do53:127.0.0.1@5301 answered SERVFAIL"

    original = dns.resolver.Resolver.resolve

    def boom(self, *a, **k):
        raise FakeServfail()

    dns.resolver.Resolver.resolve = boom
    try:
        return status_of(lambda: client.discover_dns("latency"))
    finally:
        dns.resolver.Resolver.resolve = original


def case_resolver_down():
    old_port = client.RESOLVER_PORT
    client.RESOLVER_PORT = 1  # nothing listens here
    try:
        return status_of(lambda: client.discover_dns("latency"))
    finally:
        client.RESOLVER_PORT = old_port


CASES = [
    ("valid call with token", "VALID", case_valid),
    ("wrong token", "UNAUTHORISED", case_unauthorised),
    ("service down (closed port)", "UNAVAILABLE", case_unavailable_service),
    ("malformed SVCB records", "MALFORMED", case_malformed),
    ("descriptor digest mismatch", "DIGEST_MISMATCH", case_digest_mismatch),
    ("resolver answers SERVFAIL", "BOGUS", case_bogus),
    ("resolver unreachable", "UNAVAILABLE", case_resolver_down),
]


def live():
    client.MODE = "dns"
    out = []
    for name in client.SERVICES:
        status, _ = client.run(name)
        out.append((f"live DNS discovery: {name}", "VALID", status))
    return out


if __name__ == "__main__":
    if not REAL_TOKEN:
        sys.exit("Set TOKEN first, e.g.  $env:TOKEN='secret123'")
    rows = [(n, exp, fn()) for n, exp, fn in CASES]
    if "--live" in sys.argv:
        rows += live()
    failed = 0
    print(f"{'case':<34}{'expected':<17}{'got':<17}result")
    for name, exp, got in rows:
        ok = got == exp
        failed += not ok
        print(f"{name:<34}{exp:<17}{got:<17}{'PASS' if ok else 'FAIL'}")
    print(f"\n{len(rows) - failed}/{len(rows)} passed")
    sys.exit(1 if failed else 0)
