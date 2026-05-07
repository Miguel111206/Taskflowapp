from behave import given, when, then
from fastapi.testclient import TestClient
from src.presentation.api.app import app

client = TestClient(app)
token = None


@given('I am logged in')
def step_logged_in(context):
    global token
    response = client.post(
        "/auth/login",
        json={"username": "testuser", "password": "TestPass123"}
    )
    if response.status_code == 200:
        token = response.json()["access_token"]


@given('I have a task with title "{title}"')
def step_have_task(context, title):
    if token is None:
        return
    response = client.post(
        "/tasks/",
        json={"title": title, "description": "Description"},
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code == 201:
        context.last_task = response.json()


@given('I have tasks')
def step_have_tasks(context):
    if token is None:
        return
    for title in ["Task 1", "Task 2"]:
        client.post(
            "/tasks/",
            json={"title": title, "description": "Description"},
            headers={"Authorization": f"Bearer {token}"}
        )


@when('I create a task with title "{title}"')
def step_create_task(context, title):
    if token is None:
        return
    response = client.post(
        "/tasks/",
        json={"title": title},
        headers={"Authorization": f"Bearer {token}"}
    )
    context.response = response
    context.status_code = response.status_code


@when('I provide description "{description}"')
def step_provide_description(context, description):
    if not hasattr(context, 'task_data'):
        context.task_data = {}
    context.task_data["description"] = description


@when('I request my tasks')
def step_request_tasks(context):
    if token is None:
        return
    response = client.get(
        "/tasks/",
        headers={"Authorization": f"Bearer {token}"}
    )
    context.response = response
    context.status_code = response.status_code


@when('I complete the task')
def step_complete_task(context):
    if token is None or not hasattr(context, 'last_task'):
        return
    task_id = context.last_task.get("id")
    if task_id:
        response = client.post(
            f"/tasks/{task_id}/complete",
            headers={"Authorization": f"Bearer {token}"}
        )
        context.response = response


@when('I delete the task')
def step_delete_task(context):
    if token is None or not hasattr(context, 'last_task'):
        return
    task_id = context.last_task.get("id")
    if task_id:
        response = client.delete(
            f"/tasks/{task_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        context.response = response


@then('the task should be created')
def step_task_created(context):
    data = context.response.json()
    assert data.get("title") is not None


@then('the task status should be "{status}"')
def step_task_status(context, status):
    data = context.response.json()
    assert data.get("status") == status


@then('I should see all my tasks')
def step_see_all_tasks(context):
    data = context.response.json()
    assert isinstance(data, list)


@then('the task should be removed')
def step_task_removed(context):
    assert context.status_code == 204