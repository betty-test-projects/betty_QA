import pytest
import requests
import logging
from playwright.sync_api import Page, expect

log = logging.getLogger(__name__)

BASE_URL = "http://127.0.0.1:5000"

def test_page_loads(page: Page):
    log.info("Navigating to Task Manager page")
    page.goto(BASE_URL)

    log.info("Verifying page title exists")
    expect(page.locator("h1")).to_contain_text("TASK_MGR")

    log.info("Verifying input field is visible")
    expect(page.locator("#new-title")).to_be_visible()

    log.info("Verifying ADD button is visible")
    expect(page.locator(".btn-add")).to_be_visible()

    log.info("test_page_loads passed")