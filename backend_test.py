# Asignado: Copilot - tests backend (ubicado en backend_test.py por entorno)
import os
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

from fastapi.testclient import TestClient
from backend.main import app as backend_app

client = TestClient(backend_app)

def test_register_login_and_task_crud():
    # Public register (dev compatibility)
    r = client.post('/public/register', json={'username': 'alice', 'password': 'secret'})
    assert r.status_code == 200
    data = r.json()
    assert data['username'] == 'alice'

    # Login (JSON endpoint)
    r = client.post('/login_json', json={'username': 'alice', 'password': 'secret'})
    assert r.status_code == 200
    token = r.json()
    assert 'access_token' in token and token['access_token']
    headers = {'Authorization': f"Bearer {token['access_token']}"}

    # Create task (authenticated)
    r = client.post('/tasks', json={'title': 'task1', 'description': 'desc1'}, headers=headers)
    assert r.status_code == 200
    task = r.json()
    tid = task['id']

    # Get task
    r = client.get(f'/tasks/{tid}', headers=headers)
    assert r.status_code == 200
    assert r.json()['id'] == tid

    # List tasks
    r = client.get('/tasks', headers=headers)
    assert r.status_code == 200
    assert any(t['id'] == tid for t in r.json())

    # Update task
    r = client.put(f'/tasks/{tid}', json={'title': 'task1b', 'description': 'desc2', 'owner': 'alice'}, headers=headers)
    assert r.status_code == 200
    assert r.json()['title'] == 'task1b'

    # Change status
    r = client.patch(f'/tasks/{tid}/status?status=done', headers=headers)
    assert r.status_code == 200
    assert r.json()['status'] == 'done'

    # List by user
    r = client.get('/tasks/by_user/alice', headers=headers)
    assert r.status_code == 200
    assert any(t['id'] == tid for t in r.json())

    # Delete
    r = client.delete(f'/tasks/{tid}', headers=headers)
    assert r.status_code == 200

    # Ensure deleted
    r = client.get(f'/tasks/{tid}', headers=headers)
    assert r.status_code == 404
