@echo off
REM Windows: run in the VS Code terminal, then open http://localhost:8000
cd /d "%~dp0backend"
if not exist .venv ( python -m venv .venv )
call .venv\Scripts\activate
pip install -q -r requirements.txt
python seed.py
uvicorn app.main:app --reload --port 8000
