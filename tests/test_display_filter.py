import pytest
import requests
import logging
from playwright.sync_api import Page, expect

log = logging.getLogger(__name__)

BASE_URL = "http://127.0.0.1:5000"


def test_page_auto_loads_tasks_on_startup(page: Page):
    # TC-008: Page auto-loads tasks on startup
    log.info("TC-008: Page auto-loads tasks on startup")

    log.info("Pre-creating 3 tasks via API")
    titles = ["Task Alpha", "Task Beta", "Task Gamma"]
    for title in titles:
        response = requests.post(f"{BASE_URL}/api/tasks", json={"title": title})
        log.info(f"Created task: '{title}' — status {response.status_code}")

    log.info("Loading the page")
    page.goto(BASE_URL)

    log.info("Verifying all 3 tasks are displayed after page load")
    expect(page.locator(".task-item")).to_have_count(3)

    log.info("Verifying stats bar: total=3, pending=3, done=0")
    expect(page.locator("#stat-total")).to_have_text("3")
    expect(page.locator("#stat-pending")).to_have_text("3")
    expect(page.locator("#stat-done")).to_have_text("0")

    log.info("TC-008 passed")


def test_empty_state_messages(page: Page):
    # TC-009: Empty list shows 'No tasks yet' when database is empty
    # TC-011: Empty filter result shows 'Nothing here' (not 'No tasks yet')
    # Note: TC-009 and TC-011 are merged here because both test empty state UI,
    # but with different triggers — one is a truly empty database,
    # the other is an empty filter result.
    log.info("TC-009 + TC-011: Empty state messages — merged test")

    log.info("Navigating to Task Manager page with empty database")
    page.goto(BASE_URL)

    log.info("TC-009: Verifying 'No tasks yet' is shown when there are no tasks")
    expect(page.locator(".empty")).to_contain_text("No tasks yet")

    log.info("TC-009: Verifying all stats show 0")
    expect(page.locator("#stat-total")).to_have_text("0")
    expect(page.locator("#stat-pending")).to_have_text("0")
    expect(page.locator("#stat-done")).to_have_text("0")

    log.info("TC-009 verified")

    log.info("Adding a pending task to set up TC-011")
    page.locator("#new-title").fill("Active only task")
    page.locator(".btn-add").click()
    expect(page.locator("#stat-total")).to_have_text("1")

    log.info("TC-011: Switching to DONE filter — no completed tasks exist")
    page.locator(".filter-btn", has_text="DONE").click()

    log.info("TC-011: Verifying 'Nothing here' is shown (not 'No tasks yet')")
    expect(page.locator(".empty")).to_contain_text("Nothing here")

    log.info("TC-011 verified")
    log.info("TC-009 + TC-011 passed")


def test_filter_tabs_all_active_done(page: Page):
    # TC-010: Filter tabs ALL / ACTIVE / DONE show correct subsets
    log.info("TC-010: Filter tabs ALL / ACTIVE / DONE show correct subsets")

    log.info("Navigating to Task Manager page")
    page.goto(BASE_URL)

    log.info("Adding 2 pending tasks via UI")
    for i, title in enumerate(["Pending Task 1", "Pending Task 2"], start=1):
        page.locator("#new-title").fill(title)
        page.locator(".btn-add").click()
        expect(page.locator("#stat-total")).to_have_text(str(i))
        log.info(f"Added and confirmed: '{title}'")

    log.info("Adding 1 task and completing it")
    page.locator("#new-title").fill("Completed Task 1")
    page.locator(".btn-add").click()
    expect(page.locator("#stat-total")).to_have_text("3")
    page.locator(".check-btn").first.click()
    expect(page.locator("#stat-done")).to_have_text("1")
    log.info("Marked 'Completed Task 1' as done")

    log.info("Verifying ALL filter shows 3 tasks")
    page.locator(".filter-btn", has_text="ALL").click()
    expect(page.locator(".task-item")).to_have_count(3)

    log.info("Verifying ACTIVE filter shows 2 tasks")
    page.locator(".filter-btn", has_text="ACTIVE").click()
    expect(page.locator(".task-item")).to_have_count(2)

    log.info("Verifying DONE filter shows 1 task")
    page.locator(".filter-btn", has_text="DONE").click()
    expect(page.locator(".task-item")).to_have_count(1)

    log.info("TC-010 passed")


def test_stats_bar_updates_in_real_time(page: Page):
    # TC-012: Stats bar updates in real time after each operation
    log.info("TC-012: Stats bar updates in real time")

    log.info("Navigating to Task Manager page")
    page.goto(BASE_URL)

    log.info("Adding 3 pending tasks via UI")
    for i, title in enumerate(["Stats Task 1", "Stats Task 2", "Stats Task 3"], start=1):
        page.locator("#new-title").fill(title)
        page.locator(".btn-add").click()
        expect(page.locator("#stat-total")).to_have_text(str(i))
        log.info(f"Added and confirmed: '{title}'")

    log.info("Verifying initial stats: total=3, done=0, pending=3")
    expect(page.locator("#stat-total")).to_have_text("3")
    expect(page.locator("#stat-done")).to_have_text("0")
    expect(page.locator("#stat-pending")).to_have_text("3")

    log.info("Completing 1 task — clicking check on 'Stats Task 3' (first in list, newest)")
    page.locator(".check-btn").first.click()
    expect(page.locator("#stat-done")).to_have_text("1")

    log.info("Verifying stats after completing 1: total=3, done=1, pending=2")
    expect(page.locator("#stat-total")).to_have_text("3")
    expect(page.locator("#stat-done")).to_have_text("1")
    expect(page.locator("#stat-pending")).to_have_text("2")

    log.info("Deleting the completed task")
    page.locator(".task-item.done .action-btn.del").click()
    expect(page.locator("#stat-total")).to_have_text("2")

    log.info("Verifying stats after deleting completed task: total=2, done=0, pending=2")
    expect(page.locator("#stat-total")).to_have_text("2")
    expect(page.locator("#stat-done")).to_have_text("0")
    expect(page.locator("#stat-pending")).to_have_text("2")

    log.info("TC-012 passed")