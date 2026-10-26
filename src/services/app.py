"""Mock diagnostic service. One app, three personalities chosen by SERVICE env var."""
import hmac, os, sys
from flask import Flask, jsonify, request

SERVICE = os.environ.get("SERVICE", "latency")
TOKEN = os.environ.get("TOKEN", "")
PORT = int(os.environ.get("PORT", "8081"))

if not TOKEN:
    sys.exit("TOKEN env var is required (refusing to start without a secret)")

SAMPLES = {
    "latency": {"service": "latency", "latency_ms": 20},
    "traceroute": {"service": "traceroute", "hops": ["10.0.0.1", "10.0.1.1", "10.0.2.5"]},
    "lossjitter": {"service": "lossjitter", "loss_percent": 0.5, "jitter_ms": 2.1},
}
if SERVICE not in SAMPLES:
    sys.exit(f"Unknown SERVICE '{SERVICE}'. Use one of: {', '.join(SAMPLES)}")

app = Flask(__name__)


@app.get("/health")
def health():
    return jsonify(status="ok", service=SERVICE)


@app.get("/.well-known/descriptor.json")
def descriptor():
    # Public metadata. Its SHA-256 digest is what the DNS record will carry (cap-sha256).
    return jsonify(name=SERVICE, version="1.0",
                   operations=[{"path": "/probe", "method": "GET", "auth": "bearer"}])


@app.get("/probe")
def probe():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify(error="missing token"), 401
    if not hmac.compare_digest(auth[7:], TOKEN):
        return jsonify(error="invalid token"), 403
    return jsonify(SAMPLES[SERVICE])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
