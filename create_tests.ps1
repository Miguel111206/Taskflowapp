$root = "C:\Users\User\taskflow_app"
$testsdir = Join-Path $root "backend\tests"
if (-not (Test-Path $testsdir)) { New-Item -ItemType Directory -Path $testsdir | Out-Null }

$test_py = @'
# Asignado: Copilot
import os
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_crud_and_status_flow():
    # Create a task
    r = client.post('/tasks', json={'title':'task1','description':'desc'})
    assert r.status_code == 200
    task = r.json()
    assert task['title'] == 'task1'
    tid = task['id']

    # Get task
    r = client.get(f'/tasks/{tid}')
    assert r.status_code == 200
    assert r.json()['id'] == tid

    # List tasks
    r = client.get('/tasks')
    assert r.status_code == 200
    assert any(t['id'] == tid for t in r.json())

    # Update task
    r = client.put(f'/tasks/{tid}', json={'title':'task1b','description':'desc2'})
    assert r.status_code == 200
    assert r.json()['title'] == 'task1b'

    # Change status
    r = client.patch(f'/tasks/{tid}/status?status=done')
    assert r.status_code == 200
    assert r.json()['status'] == 'done'

    # List by status
    r = client.get('/tasks/by_status/done')
    assert r.status_code == 200
    assert any(t['id'] == tid for t in r.json())

    # Delete
    r = client.delete(f'/tasks/{tid}')
    assert r.status_code == 200

    # Ensure deleted
    r = client.get(f'/tasks/{tid}')
    assert r.status_code == 404
'@

$test_py | Out-File -FilePath (Join-Path $testsdir "test_api.py") -Encoding utf8
Write-Output "Created $testsdir\test_api.py"
