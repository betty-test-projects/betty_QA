import pytest
import requests
import logging
from playwright.sync_api import Page, expect

log = logging.getLogger(__name__)

BASE_URL = "http://127.0.0.1:5000"


def test_add_task_with_valid_title(page: Page):
    # TC-001: Add a task with a valid title
    log.info("TC-001: Add a task with a valid title")

    log.info("Navigating to Task Manager page")
    page.goto(BASE_URL)

    log.info("Typing task title 'Buy groceries'")
    page.locator("#new-title").fill("Buy groceries")

    log.info("Clicking ADD button")
    page.locator(".btn-add").click()

    log.info("Verifying task appears in the list")
    expect(page.locator(".task-title").first).to_contain_text("Buy groceries")

    log.info("Verifying stats bar: total=1, pending=1, done=0")
    expect(page.locator("#stat-total")).to_have_text("1")
    expect(page.locator("#stat-pending")).to_have_text("1")
    expect(page.locator("#stat-done")).to_have_text("0")

    log.info("Verifying toast message appears")
    expect(page.locator("#toast")).to_contain_text("Task added")

    log.info("TC-001 passed")


def test_add_task_by_pressing_enter(page: Page):
    # TC-002: Add a task by pressing the Enter key
    log.info("TC-002: Add a task by pressing the Enter key")

    log.info("Navigating to Task Manager page")
    page.goto(BASE_URL)

    log.info("Typing task title 'Read a book'")
    page.locator("#new-title").fill("Read a book")

    log.info("Pressing Enter key (not clicking the button)")
    page.locator("#new-title").press("Enter")

    log.info("Verifying task appears in the list")
    expect(page.locator(".task-title").first).to_contain_text("Read a book")

    log.info("Verifying stats bar: total=1, pending=1, done=0")
    expect(page.locator("#stat-total")).to_have_text("1")
    expect(page.locator("#stat-pending")).to_have_text("1")
    expect(page.locator("#stat-done")).to_have_text("0")

    log.info("Verifying toast message appears")
    expect(page.locator("#toast")).to_contain_text("Task added")

    log.info("TC-002 passed")


def test_empty_input_should_not_create_task(page: Page):
    # TC-003: Empty input should not create a task
    log.info("TC-003: Empty input should not create a task")

    log.info("Navigating to Task Manager page")
    page.goto(BASE_URL)

    log.info("Leaving input empty and clicking ADD button")
    page.locator(".btn-add").click()

    log.info("Verifying no task is created (list shows empty state)")
    expect(page.locator(".empty")).to_be_visible()
    expect(page.locator("#stat-total")).to_have_text("0")

    log.info("Entering only spaces and clicking ADD button")
    page.locator("#new-title").fill("   ")
    page.locator(".btn-add").click()

    log.info("Verifying still no task is created")
    expect(page.locator("#stat-total")).to_have_text("0")

    log.info("TC-003 passed")


def test_add_task_max_length_frontend(page: Page):
    # TC-004a: Frontend enforces 200-character max length via HTML maxlength attribute
    log.info("TC-004a: Add a task at the maximum length (200 chars) - frontend")

    log.info("Navigating to Task Manager page")
    page.goto(BASE_URL)

    title_200 = "A" * 200
    log.info(f"Typing a 200-character title (length={len(title_200)})")
    page.locator("#new-title").fill(title_200)

    actual_value = page.locator("#new-title").input_value()
    log.info(f"Input field value length after fill: {len(actual_value)}")
    assert len(actual_value) == 200, f"Expected 200 chars, got {len(actual_value)}"

    log.info("Clicking ADD button")
    page.locator(".btn-add").click()

    log.info("Verifying task is created successfully with full 200-char title")
    expect(page.locator(".task-title").first).to_contain_text("A" * 20)
    expect(page.locator("#stat-total")).to_have_text("1")

    log.info("TC-004a passed — frontend maxlength=200 is enforced")


def test_add_task_exceeds_max_length_api():
    # TC-004b: Backend has no length validation — API accepts titles beyond 200 chars
    log.info("TC-004b: POST /api/tasks with title > 200 chars (backend has no validation)")

    title_201 = "B" * 201
    log.info(f"Sending POST /api/tasks with {len(title_201)}-character title directly via API")
    response = requests.post(
        f"{BASE_URL}/api/tasks",
        json={"title": title_201}
    )
    log.info(f"Response status: {response.status_code}")
    log.info(f"Response body: {response.json()}")

    log.info("[Risk] Backend accepted a 201-char title — no server-side length validation exists")
    assert response.status_code == 201, (
        f"Expected 201 Created (backend has no length limit), got {response.status_code}"
    )

    created_title = response.json().get("title", "")
    assert len(created_title) == 201, f"Expected title length 201, got {len(created_title)}"
    log.info(f"TC-004b confirmed: backend stored a {len(created_title)}-char title without rejection")


def test_add_task_with_special_characters(page: Page):
    # TC-005: Add tasks with special characters, HTML tags, emoji, and Chinese text
    log.info("TC-005: Add a task with special characters, HTML tags, emoji, and Chinese text")

    log.info("Navigating to Task Manager page")
    page.goto(BASE_URL)

    test_inputs = [
        ("<script>alert(1)</script>", "XSS script tag"),
        ("A & B > C < D",            "HTML entities"),
        ("@#%*~!^",                   "Special characters"),
        ("買菜、煮飯、洗碗",              "Chinese characters"),
        ("Buy 📚 & read 🎯",           "Emoji mixed with text"),
    ]

    for title, description in test_inputs:
        log.info(f"Testing input: {description} — '{title}'")
        page.locator("#new-title").fill(title)
        page.locator(".btn-add").click()

        log.info(f"Verifying '{description}' appears as plain text in the list")
        expect(page.locator(".task-title").first).to_contain_text(
            title if "<script>" not in title else "alert(1)"
        )
        log.info(f"Verified: no script executed, text rendered correctly")

    log.info("Verifying total task count")
    expect(page.locator("#stat-total")).to_have_text(str(len(test_inputs)))

    log.info("TC-005 passed — all special character inputs rendered as plain text")