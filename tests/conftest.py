import pytest
import requests
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
log = logging.getLogger(__name__)

BASE_URL = "http://127.0.0.1:5000"


@pytest.fixture(autouse=True)
def clean_state():
    log.info("=== Test starting: clearing all tasks ===")
    tasks = requests.get(f"{BASE_URL}/api/tasks").json()
    log.info(f"Found {len(tasks)} task(s), deleting all")
    for task in tasks:
        requests.delete(f"{BASE_URL}/api/tasks/{task['id']}")
        log.info(f"Deleted task id={task['id']} title='{task['title']}'")
    log.info("Clean up complete, starting test")
    yield
    log.info("=== Test finished: clearing all tasks ===")
    tasks = requests.get(f"{BASE_URL}/api/tasks").json()
    for task in tasks:
        requests.delete(f"{BASE_URL}/api/tasks/{task['id']}")
    log.info("Clean up complete")