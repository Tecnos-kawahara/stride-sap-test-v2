"""
pytest-playwright Configuration for E2E Tests

Template Version: 6.0.0-tecnos-stride-value

This conftest.py should be placed in specs/<feature>/tests/e2e/

Usage:
    pytest specs/<feature>/tests/e2e/ --headed
    pytest specs/<feature>/tests/e2e/ --browser chromium --slowmo 500
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Generator

import pytest
from playwright.sync_api import Browser, BrowserContext, Page, Playwright


# =============================================================================
# Configuration
# =============================================================================

# Base URL for the application under test
BASE_URL = os.getenv("E2E_BASE_URL", "http://localhost:8000")

# Browser settings
HEADLESS = os.getenv("E2E_HEADLESS", "true").lower() == "true"
SLOW_MO = int(os.getenv("E2E_SLOW_MO", "0"))  # milliseconds between actions

# Viewport settings
VIEWPORT_WIDTH = 1280
VIEWPORT_HEIGHT = 720


# =============================================================================
# Browser Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def browser_context_args() -> dict:
    """Configure browser context arguments.

    Returns settings for viewport, locale, timezone, etc.
    """
    return {
        "viewport": {"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT},
        "locale": "ja-JP",
        "timezone_id": "Asia/Tokyo",
        "ignore_https_errors": True,
        # Storage state for authenticated sessions (optional)
        # "storage_state": "auth_state.json",
    }


@pytest.fixture(scope="session")
def browser_type_launch_args() -> dict:
    """Configure browser launch arguments."""
    return {
        "headless": HEADLESS,
        "slow_mo": SLOW_MO,
    }


# =============================================================================
# Page Fixtures
# =============================================================================

@pytest.fixture(scope="function")
def page(context: BrowserContext) -> Generator[Page, None, None]:
    """Provide a fresh page for each test.

    The page automatically navigates to BASE_URL before the test.
    """
    page = context.new_page()
    page.goto(BASE_URL)
    yield page
    page.close()


# =============================================================================
# Authentication Fixtures
# =============================================================================

@pytest.fixture(scope="function")
def buyer_page(context: BrowserContext) -> Generator[Page, None, None]:
    """Provide a page authenticated as a buyer user."""
    page = context.new_page()
    _login(page, email="buyer@example.com", password="buyerPass123")
    yield page
    page.close()


@pytest.fixture(scope="function")
def supplier_page(context: BrowserContext) -> Generator[Page, None, None]:
    """Provide a page authenticated as a supplier user."""
    page = context.new_page()
    _login(page, email="supplier@example.com", password="supplierPass123")
    yield page
    page.close()


def _login(page: Page, email: str, password: str) -> None:
    """Helper function to perform login."""
    page.goto(f"{BASE_URL}/login")
    page.fill('input[name="email"]', email)
    page.fill('input[name="password"]', password)
    page.click('button[type="submit"]')
    page.wait_for_url("**/dashboard**")


# =============================================================================
# Test Data Fixtures
# =============================================================================

@pytest.fixture(scope="function")
def test_order_data() -> dict:
    """Provide test data for order creation."""
    return {
        "order_number": "TEST-001",
        "items": [
            {"name": "Test Item 1", "quantity": 10, "unit_price": 100},
            {"name": "Test Item 2", "quantity": 5, "unit_price": 200},
        ],
        "delivery_date": "2025-12-31",
        "notes": "Test order for E2E testing",
    }


# =============================================================================
# Screenshot & Trace on Failure
# =============================================================================

@pytest.fixture(autouse=True)
def auto_screenshot_on_failure(page: Page, request: pytest.FixtureRequest):
    """Automatically capture screenshot on test failure."""
    yield

    # Check if test failed
    if hasattr(request.node, "rep_call") and request.node.rep_call.failed:
        # Create reports directory if needed
        # Path relative to this file: specs/<feature>/tests/e2e/ -> specs/<feature>/tests/reports/e2e/
        reports_dir = Path(__file__).parent.parent / "reports" / "e2e"
        reports_dir.mkdir(parents=True, exist_ok=True)

        # Capture screenshot
        screenshot_path = reports_dir / f"{request.node.name}.png"
        page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"\n📸 Screenshot saved: {screenshot_path}")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Store test result for use in fixtures."""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


# =============================================================================
# Console Log Capture
# =============================================================================

@pytest.fixture(scope="function")
def capture_console(page: Page) -> Generator[list, None, None]:
    """Capture browser console messages.

    Usage:
        def test_example(page, capture_console):
            page.goto("/")
            page.click("button")
            assert not any("error" in msg.lower() for msg in capture_console)
    """
    messages: list[str] = []

    def handle_console(msg):
        messages.append(f"[{msg.type}] {msg.text}")

    page.on("console", handle_console)
    yield messages


# =============================================================================
# Network Request Interception
# =============================================================================

@pytest.fixture(scope="function")
def mock_api_response(page: Page):
    """Mock API responses for isolated testing.

    Usage:
        def test_with_mock(page, mock_api_response):
            mock_api_response("/api/orders", {"orders": []})
            page.goto("/orders")
    """
    def _mock(url_pattern: str, response_data: dict, status: int = 200):
        page.route(
            url_pattern,
            lambda route: route.fulfill(
                status=status,
                content_type="application/json",
                body=str(response_data),
            ),
        )

    return _mock
