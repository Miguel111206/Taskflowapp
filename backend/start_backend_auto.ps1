# Start backend on first available port from 8000..8010
# Asignado: Copilot
$ports = 8000..8010

# Activate virtualenv if present
if (Test-Path .\.venv\Scripts\Activate.ps1) {
    Write-Output "Activating virtualenv"
    . .\.venv\Scripts\Activate.ps1
}

$free = $null
foreach ($p in $ports) {
    try {
        $res = Test-NetConnection -ComputerName 127.0.0.1 -Port $p -WarningAction SilentlyContinue
        if ($res -and $res.TcpTestSucceeded -eq $false) {
            $free = $p
            break
        }
    } catch {
        # In some environments Test-NetConnection may not be available; assume port free and try
        $free = $p
        break
    }
}

if (-not $free) {
    Write-Error "No free port found in range 8000..8010. Please free a port or edit the script."
    exit 1
}

Write-Output "Starting uvicorn on port $free"
# Ensure uvicorn is available in the venv; otherwise run pip install -r requirements.txt first
uvicorn main:app --reload --host 127.0.0.1 --port $free
