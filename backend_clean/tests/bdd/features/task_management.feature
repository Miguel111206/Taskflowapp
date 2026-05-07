Feature: Task Management
    As a user
    I want to manage my tasks
    So that I can track my work

    Scenario: Create a new task
        Given I am logged in
        When I create a task with title "New Task"
        And I provide description "Task description"
        Then the task should be created
        And the task status should be "pending"

    Scenario: List my tasks
        Given I have tasks
        When I request my tasks
        Then I should see all my tasks

    Scenario: Complete a task
        Given I have a task with title "Task to Complete"
        When I complete the task
        Then the task status should be "completed"

    Scenario: Delete a task
        Given I have a task
        When I delete the task
        Then the task should be removed