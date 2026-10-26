# PS-033 starter (Student B: services + client)

## Run the services
    cp .env.example .env        # then edit TOKEN to a random string
    docker compose up --build   # latency:8081  traceroute:8082  lossjitter:8083

## Run the client (static mode, no DNS needed)
    pip install -r client/requirements.txt
    export TOKEN=<same token as .env>
    python client/client.py

Without Docker, run each service directly:
    SERVICE=latency PORT=8081 TOKEN=<token> python services/app.py

## Outcomes the client reports
VALID, INSECURE, BOGUS, MALFORMED, UNAVAILABLE, UNAUTHORISED

## Switching to DNS mode (once Student A's resolver is up)
    MODE=dns RESOLVER_IP=<resolver ip> ZONE=lab.test python client/client.py
DNS mode is UNTESTED against a real resolver. Only its record parser has been tested.

## Try the failure cases
- UNAUTHORISED: run the client with no TOKEN or a wrong one
- UNAVAILABLE:  stop one service container
