#!/usr/bin/env python3
"""Re-export BIND's KSK as Unbound's trust anchor, then restart Unbound.
Cross-platform: runs dig inside the lab-bind container, so the host needs only Docker + Python."""
import pathlib
import subprocess
import sys

root = pathlib.Path(__file__).resolve().parent

res = subprocess.run(
    ["docker", "exec", "lab-bind", "dig", "@127.0.0.1", "lab.test",
     "DNSKEY", "+noall", "+answer"],
    capture_output=True, text=True,
)
if res.returncode != 0:
    sys.exit("docker exec failed (is lab-bind running?):\n" + res.stderr)

ksk = [l for l in res.stdout.splitlines()
       if len(l.split()) > 4 and l.split()[3] == "DNSKEY" and l.split()[4] == "257"]
if not ksk:
    sys.exit("No KSK (flags 257) found. Wait ~10 s after 'docker compose up -d' and retry.")

(root / "unbound").mkdir(exist_ok=True)
(root / "unbound" / "lab.test.key").write_text(ksk[0] + "\n")
print(ksk[0])

subprocess.run(["docker", "compose", "restart", "unbound"], cwd=root, check=True)
