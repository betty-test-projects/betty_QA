import pytest
import requests
import logging
from playwright.sync_api import Page, expect

log = logging.getLogger(__name__)

BASE_URL = "http://127.0.0.1:5000"


def test_delete_a_task_successfully(page: Page):
    # TC-019: Delete a task successfully
    log.info("TC-019: Delete a task successfully")

    log.info("Navigating to Task Manager page")
    page.goto(BASE_URL)

    log.info("Adding a task to delete")
    page.locator("#new-title").fill("Task to delete")
    page.locator(".btn-add").click()
    expect(page.locator("#stat-total")).to_have_text("1")

    log.info("Clicking 'del' button")
    page.locator(".action-btn.del").first.click()

    log.info("Verifying task is removed from list")
    expect(page.locator(".empty")).to_be_visible()

    log.info("Verifying stats updated: total=0, pending=0, done=0")
    expect(page.locator("#stat-total")).to_have_text("0")
    expect(page.locator("#stat-pending")).to_have_text("0")
    expect(page.locator("#stat-done")).to_have_text("0")

    log.info("Verifying toast 'Task deleted'")
    expect(page.locator("#toast")).to_contain_text("Task deleted")

    log.info("TC-019 passed")


def test_delete_nonexistent_task_returns_404():
    # TC-020: Delete a non-existent task ID returns 404 (API level)
    log.info("TC-020: DELETE /api/tasks/99999 should return 404")

    log.info("Sending DELETE /api/tasks/99999 directly via API")
    response = requests.delete(f"{BASE_URL}/api/tasks/99999")

    log.info(f"Response status: {response.status_code}")
    log.info(f"Response body: {response.json()}")

    log.info("Verifying response status is 404")
    assert response.status_code == 404, (
        f"Expected 404, got {response.status_code}"
    )

    log.info("Verifying response body contains error message")
    assert response.json() == {"error": "Task not found"}, (
        f"Unexpected response body: {response.json()}"
    )

    log.info("TC-020 passed")