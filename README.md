# AIORI-3-HACKATHON-PROJECTS
YouTube Video: https://youtu.be/odZoZYz6mRk

## How to run
Needs Docker + Python 3 (pip3 install -r src/client/requirements.txt). One laptop only.
1. cd src/dns && mkdir -p data && chmod 777 data && docker compose up -d && sleep 10 && python3 export-anchor.py
2. cd ../.. && docker compose -f src/docker-compose.yml up -d
3. cd src/client && python3 test_cases.py --live   # expect 12/12 passed

This repository will contain the code and resources for the AIORI-3 hackathon that will be developed during the AIORI-3

## Demo

Screen demo: https://drive.google.com/file/d/1yV3lZ6Ve1I8gOTpg-BtkEt3fT1PoQp-o/view?usp=drivesdk
