Feature: User Registration
    As a new user
    I want to register an account
    So that I can use the task management system

    Scenario: Register with valid credentials
        Given I am on the registration page
        When I fill in username "newuser"
        And I fill in email "newuser@example.com"
        And I fill in password "SecurePass123"
        And I submit the registration form
        Then I should see a success message

    Scenario: Register with duplicate username
        Given a user with username "existinguser" already exists
        When I try to register with username "existinguser"
        Then I should see an error message "Username already exists"