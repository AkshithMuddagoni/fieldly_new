#!/usr/bin/env bash
# Mac/Linux: ./run.sh  then open http://localhost:8000
set -e; cd "$(dirname "$0")/backend"
[ -d .venv ] || python3 -m venv .venv
. .venv/bin/activate; pip install -q -r requirements.txt
python seed.py; uvicorn app.main:app --reload --port 8000
