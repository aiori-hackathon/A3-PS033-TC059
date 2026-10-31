# AIORI-3-HACKATHON-PROJECTS

This repository will contain the code and resources for the AIORI-3 hackathon that will be developed during the AIORI-3

YouTube Video: https://youtu.be/odZoZYz6mRk

## How to run

Needs Docker + Python 3 (pip3 install -r src/client/requirements.txt). One laptop only.
TOKEN is any shared value; the services and the test must use the same one (we use secret123).
1. cd src/dns && mkdir -p data && chmod 777 data && docker compose up -d && sleep 10 && python3 export-anchor.py
2. cd ../.. && export TOKEN=secret123 && docker compose -f src/docker-compose.yml up -d
   (Windows PowerShell: $env:TOKEN='secret123')
3. cd src/client && python3 test_cases.py --live   # expect 12/12 passed

## Demo

Screen demo: https://drive.google.com/file/d/1yV3lZ6Ve1I8gOTpg-BtkEt3fT1PoQp-o/view?usp=drivesdk
