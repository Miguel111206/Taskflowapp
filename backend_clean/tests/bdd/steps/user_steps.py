from behave import given, when, then
from fastapi.testclient import TestClient
from src.presentation.api.app import app

client = TestClient(app)


@given('I am on the registration page')
def step_on_registration_page(context):
    context.path = "/auth/register"
    context.method = "POST"


@given('a user with username "{username}" already exists')
def step_user_already_exists(context, username):
    client.post(
        "/auth/register",
        json={
            "username": username,
            "email": f"{username}@example.com",
            "password": "SecurePass123"
        }
    )


@when('I fill in username "{username}"')
def step_fill_username(context, username):
    if not hasattr(context, 'data'):
        context.data = {}
    context.data["username"] = username


@when('I fill in email "{email}"')
def step_fill_email(context, email):
    if not hasattr(context, 'data'):
        context.data = {}
    context.data["email"] = email


@when('I fill in password "{password}"')
def step_fill_password(context, password):
    if not hasattr(context, 'data'):
        context.data = {}
    context.data["password"] = password


@when('I submit the registration form')
def step_submit_form(context):
    response = client.post(context.path, json=context.data)
    context.response = response
    context.status_code = response.status_code
    if hasattr(response, 'json'):
        context.response_data = response.json()


@then('I should see a success message')
def step_success_message(context):
    assert context.status_code == 201
    data = context.response.json()
    assert data.get("success") is True


@then('I should be logged in')
def step_logged_in(context):
    data = context.response.json()
    assert "data" in data


@then('I should see an error message "{message}"')
def step_error_message(context, message):
    assert context.status_code == 400
    data = context.response.json()
    assert "detail" in data or "error" in data


@given('I try to register with username "{username}"')
def step_try_register(context, username):
    client.post(
        "/auth/register",
        json={
            "username": username,
            "email": f"{username}@example.com",
            "password": "SecurePass123"
        }
    )


@when('I try to login with username "{username}" and password "{password}"')
def step_login(context, username, password):
    response = client.post(
        "/auth/login",
        json={"username": username, "password": password}
    )
    context.response = response
    context.status_code = response.status_code


@then('I should receive access and refresh tokens')
def step_receive_tokens(context):
    data = context.response.json()
    assert "access_token" in data
    assert "refresh_token" in data