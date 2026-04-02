import pytest
import requests
import logging

log = logging.getLogger(__name__)

BASE_URL = "http://127.0.0.1:5000"


def test_get_tasks_returns_correct_format():
    # TC-022: GET /api/tasks returns correct format
    log.info("TC-022: GET /api/tasks returns correct format")

    log.info("Sending GET /api/tasks")
    response = requests.get(f"{BASE_URL}/api/tasks")

    log.info(f"Response status: {response.status_code}")
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}"
    )

    body = response.json()
    log.info(f"Response body type: {type(body).__name__}")
    assert isinstance(body, list), f"Expected a JSON array, got {type(body).__name__}"

    if len(body) > 0:
        task = body[0]
        log.info(f"Verifying fields on first task: {task}")
        assert isinstance(task.get("id"), int), "Field 'id' should be an int"
        assert isinstance(task.get("title"), str), "Field 'title' should be a str"
        assert task.get("completed") in (0, 1), "Field 'completed' should be 0 or 1"
        assert isinstance(task.get("created_at"), str), "Field 'created_at' should be a str"
        log.info("All required fields are present with correct types")
    else:
        log.info("Task list is empty — creating one task to verify field structure")
        create_response = requests.post(
            f"{BASE_URL}/api/tasks", json={"title": "Format check task"}
        )
        assert create_response.status_code == 201
        task = create_response.json()
        log.info(f"Created task: {task}")
        assert isinstance(task.get("id"), int), "Field 'id' should be an int"
        assert isinstance(task.get("title"), str), "Field 'title' should be a str"
        assert task.get("completed") in (0, 1), "Field 'completed' should be 0 or 1"
        assert isinstance(task.get("created_at"), str), "Field 'created_at' should be a str"
        log.info("All required fields are present with correct types")

    log.info("TC-022 passed")


def test_post_with_missing_title_returns_400():
    # TC-023: POST with missing title returns 400
    log.info("TC-023: POST with missing title returns 400")

    log.info("Case 1: POST with empty body {}")
    response = requests.post(
        f"{BASE_URL}/api/tasks",
        json={}
    )
    log.info(f"Response status: {response.status_code}, body: {response.json()}")
    assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    assert response.json() == {"error": "Title is required"}, (
        f"Unexpected response body: {response.json()}"
    )
    log.info("Case 1 passed")

    log.info("Case 2: POST with empty title string")
    response = requests.post(
        f"{BASE_URL}/api/tasks",
        json={"title": ""}
    )
    log.info(f"Response status: {response.status_code}, body: {response.json()}")
    assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    assert response.json() == {"error": "Title is required"}, (
        f"Unexpected response body: {response.json()}"
    )
    log.info("Case 2 passed")

    log.info("Case 3: POST with plain-text (non-JSON) body")
    response = requests.post(
        f"{BASE_URL}/api/tasks",
        data="this is not json",
        headers={"Content-Type": "text/plain"}
    )
    log.info(f"Response status: {response.status_code}")
    assert response.status_code in (400, 415), (
        f"Expected 400 or 415, got {response.status_code}"
    )
    log.info("Case 3 passed")

    log.info("TC-023 passed")


def test_put_nonexistent_task_returns_404():
    # TC-024: PUT to a non-existent task ID returns 404
    log.info("TC-024: PUT /api/tasks/99999 should return 404")

    log.info("Sending PUT /api/tasks/99999 with body {\"title\": \"test\"}")
    response = requests.put(
        f"{BASE_URL}/api/tasks/99999",
        json={"title": "test"}
    )

    log.info(f"Response status: {response.status_code}")
    log.info(f"Response body: {response.json()}")

    assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    assert response.json() == {"error": "Task not found"}, (
        f"Unexpected response body: {response.json()}"
    )

    log.info("TC-024 passed")


def test_invalid_completed_field_should_return_400():
    # TC-025: Invalid 'completed' field values should return 400
    # [Bug] Backend calls int() directly without validation.
    # Passing "yes" raises ValueError -> HTTP 500.
    # Expected behavior: backend should validate input and return 400.
    # This test is written against the EXPECTED behavior and will FAIL
    # until the bug is fixed in app.py.
    log.info("TC-025: Invalid 'completed' field values should return 400 [Bug]")

    log.info("Pre-creating a task to update")
    create_response = requests.post(
        f"{BASE_URL}/api/tasks", json={"title": "Task for completed validation"}
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]
    log.info(f"Created task id={task_id}")

    invalid_cases = [
        ("yes",  "string value"),
        (2,      "out-of-range integer"),
        (-1,     "negative integer"),
    ]

    for value, description in invalid_cases:
        log.info(f"Case: completed={value!r} ({description})")
        response = requests.put(
            f"{BASE_URL}/api/tasks/{task_id}",
            json={"completed": value}
        )
        log.info(f"Response status: {response.status_code}")
        assert response.status_code == 400, (
            f"[Bug] Expected 400 for completed={value!r}, got {response.status_code}. "
            f"Backend has no input validation on 'completed' field."
        )
        log.info(f"Case passed: {description}")

    log.info("TC-025 passed")


def test_unsupported_http_methods_return_405():
    # TC-026: Unsupported HTTP methods return 405
    log.info("TC-026: Unsupported HTTP methods should return 405")

    log.info("Case 1: PATCH /api/tasks (not defined)")
    response = requests.patch(f"{BASE_URL}/api/tasks")
    log.info(f"Response status: {response.status_code}")
    assert response.status_code == 405, f"Expected 405, got {response.status_code}"
    log.info("Case 1 passed")

    log.info("Case 2: DELETE /api/tasks (without an ID)")
    response = requests.delete(f"{BASE_URL}/api/tasks")
    log.info(f"Response status: {response.status_code}")
    assert response.status_code == 405, f"Expected 405, got {response.status_code}"
    log.info("Case 2 passed")

    log.info("TC-026 passed")