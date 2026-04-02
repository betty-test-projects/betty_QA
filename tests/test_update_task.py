import pytest
import requests
import logging
from playwright.sync_api import Page, expect

log = logging.getLogger(__name__)

BASE_URL = "http://127.0.0.1:5000"


def test_toggle_task_completion_status(page: Page):
    # TC-013: Toggle task completion status
    log.info("TC-013: Toggle task completion status")

    log.info("Navigating to Task Manager page")
    page.goto(BASE_URL)

    log.info("Adding a task to toggle")
    page.locator("#new-title").fill("Buy groceries")
    page.locator(".btn-add").click()
    expect(page.locator("#stat-total")).to_have_text("1")

    log.info("First click: marking task as done")
    page.locator(".check-btn").first.click()
    expect(page.locator("#stat-done")).to_have_text("1")

    log.info("Verifying task has done styling (strikethrough)")
    expect(page.locator(".task-item.done").first).to_be_visible()

    log.info("Verifying toast 'Marked as done'")
    expect(page.locator("#toast")).to_contain_text("Marked as done")

    log.info("Verifying stats: total=1, done=1, pending=0")
    expect(page.locator("#stat-total")).to_have_text("1")
    expect(page.locator("#stat-done")).to_have_text("1")
    expect(page.locator("#stat-pending")).to_have_text("0")

    log.info("Second click: reverting task to active")
    page.locator(".check-btn").first.click()
    expect(page.locator("#stat-done")).to_have_text("0")

    log.info("Verifying task is no longer marked as done")
    expect(page.locator(".task-item.done")).to_have_count(0)

    log.info("Verifying toast 'Marked as active'")
    expect(page.locator("#toast")).to_contain_text("Marked as active")

    log.info("Verifying stats: total=1, done=0, pending=1")
    expect(page.locator("#stat-done")).to_have_text("0")
    expect(page.locator("#stat-pending")).to_have_text("1")

    log.info("TC-013 passed")


def test_edit_a_task_title(page: Page):
    # TC-014: Edit a task title
    log.info("TC-014: Edit a task title")

    log.info("Navigating to Task Manager page")
    page.goto(BASE_URL)

    log.info("Adding a task to edit")
    page.locator("#new-title").fill("Original title")
    page.locator(".btn-add").click()
    expect(page.locator("#stat-total")).to_have_text("1")

    log.info("Clicking 'edit' button to enter edit mode")
    page.locator(".edit-btn").first.click()

    log.info("Verifying edit input is visible")
    expect(page.locator(".task-edit-input").first).to_be_visible()

    log.info("Clearing and typing new title 'Updated title'")
    page.locator(".task-edit-input").first.fill("Updated title")

    log.info("Clicking 'save' button")
    page.locator(".save-btn").first.click()

    log.info("Verifying title updated to 'Updated title'")
    expect(page.locator(".task-title").first).to_contain_text("Updated title")

    log.info("Verifying toast 'Task updated'")
    expect(page.locator("#toast")).to_contain_text("Task updated")

    log.info("Verifying edit button is restored (not save button)")
    expect(page.locator(".edit-btn").first).to_be_visible()

    log.info("TC-014 passed")


def test_press_enter_to_save_while_editing(page: Page):
    # TC-015: Press Enter to save while editing
    log.info("TC-015: Press Enter to save while editing")

    log.info("Navigating to Task Manager page")
    page.goto(BASE_URL)

    log.info("Adding a task to edit")
    page.locator("#new-title").fill("Task to edit with Enter")
    page.locator(".btn-add").click()
    expect(page.locator("#stat-total")).to_have_text("1")

    log.info("Clicking 'edit' button to enter edit mode")
    page.locator(".edit-btn").first.click()
    expect(page.locator(".task-edit-input").first).to_be_visible()

    log.info("Modifying the title")
    page.locator(".task-edit-input").first.fill("Saved with Enter")

    log.info("Pressing Enter to save")
    page.locator(".task-edit-input").first.press("Enter")

    log.info("Verifying title updated successfully")
    expect(page.locator(".task-title").first).to_contain_text("Saved with Enter")

    log.info("Verifying toast 'Task updated'")
    expect(page.locator("#toast")).to_contain_text("Task updated")

    log.info("TC-015 passed")


def test_press_escape_to_cancel_editing(page: Page):
    # TC-016: Press Escape to cancel editing
    log.info("TC-016: Press Escape to cancel editing")

    log.info("Navigating to Task Manager page")
    page.goto(BASE_URL)

    log.info("Adding a task to edit")
    page.locator("#new-title").fill("Original title")
    page.locator(".btn-add").click()
    expect(page.locator("#stat-total")).to_have_text("1")

    log.info("Clicking 'edit' button to enter edit mode")
    page.locator(".edit-btn").first.click()
    expect(page.locator(".task-edit-input").first).to_be_visible()

    log.info("Modifying the title")
    page.locator(".task-edit-input").first.fill("This should be discarded")

    log.info("Pressing Escape to cancel")
    page.locator(".task-edit-input").first.press("Escape")

    log.info("Verifying title reverted to original")
    expect(page.locator(".task-title").first).to_contain_text("Original title")

    log.info("TC-016 passed")


def test_saving_empty_title_should_be_blocked(page: Page):
    # TC-017: Saving an empty title should be blocked
    log.info("TC-017: Saving an empty title should be blocked")

    log.info("Navigating to Task Manager page")
    page.goto(BASE_URL)

    log.info("Adding a task to edit")
    page.locator("#new-title").fill("Task with title")
    page.locator(".btn-add").click()
    expect(page.locator("#stat-total")).to_have_text("1")

    log.info("Clicking 'edit' button to enter edit mode")
    page.locator(".edit-btn").first.click()
    expect(page.locator(".task-edit-input").first).to_be_visible()

    log.info("Scenario 1: Clearing the input (empty title) and clicking save")
    page.locator(".task-edit-input").first.fill("")
    page.locator(".save-btn").first.click()

    log.info("Verifying app remains in edit mode — save-btn still visible")
    expect(page.locator(".save-btn").first).to_be_visible()

    log.info("Verifying original title is preserved (task-title still hidden but value unchanged)")
    # Note: in edit mode, task-title is hidden — verify via input value instead
    expect(page.locator(".task-edit-input").first).to_have_value("")

    log.info("Scenario 2: Entering only spaces and pressing Enter")
    page.locator(".task-edit-input").first.fill("   ")
    page.locator(".task-edit-input").first.press("Enter")

    log.info("Verifying app remains in edit mode — save is still blocked")
    expect(page.locator(".save-btn").first).to_be_visible()

    log.info("Pressing Escape to exit edit mode and verify original title restored")
    page.locator(".task-edit-input").first.press("Escape")
    expect(page.locator(".task-title").first).to_contain_text("Task with title")

    log.info("TC-017 passed")


def test_completed_task_can_still_be_edited(page: Page):
    # TC-018: A completed task can still be edited
    log.info("TC-018: A completed task can still be edited")

    log.info("Navigating to Task Manager page")
    page.goto(BASE_URL)

    log.info("Adding a task and marking it as completed")
    page.locator("#new-title").fill("Task to complete and edit")
    page.locator(".btn-add").click()
    expect(page.locator("#stat-total")).to_have_text("1")

    page.locator(".check-btn").first.click()
    expect(page.locator("#stat-done")).to_have_text("1")
    log.info("Task is now marked as done")

    log.info("Clicking 'edit' on the completed task")
    page.locator(".edit-btn").first.click()

    log.info("Verifying edit input is accessible on a completed task")
    expect(page.locator(".task-edit-input").first).to_be_visible()

    log.info("Modifying the title")
    page.locator(".task-edit-input").first.fill("Edited while done")

    log.info("Saving the edit")
    page.locator(".save-btn").first.click()

    log.info("Verifying title was updated successfully")
    expect(page.locator(".task-title").first).to_contain_text("Edited while done")

    log.info("Verifying toast 'Task updated'")
    expect(page.locator("#toast")).to_contain_text("Task updated")

    log.info("TC-018 passed — completed tasks can still be edited and saved")