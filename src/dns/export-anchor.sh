#!/bin/sh
# Re-export BIND's KSK as Unbound's trust anchor, then restart Unbound
cd "$(dirname "$0")"
dig @127.0.0.1 -p 5300 lab.test DNSKEY +noall +answer | grep '257 3' > unbound/lab.test.key
cat unbound/lab.test.key
docker compose restart unbound
