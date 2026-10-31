from __future__ import annotations

import pytest

from dashboard import app as app_module
from dashboard.geo import clear_cache


@pytest.fixture(autouse=True)
def clean_dashboard_state():
    app_module.app.config.update(TESTING=True, SECRET_KEY="test-secret")
    with app_module._recent_lock:
        app_module._recent.clear()
    while not app_module._geo_queue.empty():
        app_module._geo_queue.get_nowait()
        app_module._geo_queue.task_done()
    clear_cache()
    yield
    with app_module._recent_lock:
        app_module._recent.clear()
    clear_cache()
