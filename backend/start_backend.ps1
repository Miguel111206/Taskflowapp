# Start backend on port 8010 (container-friendly)
$env:PYTHONUNBUFFERED = "1"
.\.venv\Scripts\Activate.ps1
uvicorn main:app --reload --host 0.0.0.0 --port 8010
