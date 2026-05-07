# Start backend on port 8000 (Codex preference)
$env:PYTHONUNBUFFERED = "1"
.\.venv\Scripts\Activate.ps1
uvicorn main:app --reload --host 127.0.0.1 --port 8000
