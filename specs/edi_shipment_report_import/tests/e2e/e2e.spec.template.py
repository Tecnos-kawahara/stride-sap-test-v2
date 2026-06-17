"""
E2E Test Template (Python/pytest-playwright)

Template Version: 6.0.0-tecnos-stride-value
Feature: FEAT-EDISHIPMENTREPORTIMPORT

This template provides a structure for E2E tests following the SDD workflow.
Each test should map to an AC with the 'e2e' tag in spec.md.

Naming Convention:
  - File: test_<scenario>.py (e.g., test_order_flow.py)
  - Test ID: TS-E2E-NN (matches plan.md test IDs)

AC Coverage:
  - Add @ac:AC-US-EDISHIPMENTREPORTIMPORT-001-01 in docstring to link to ACs
  - This enables traceability from test to spec

Usage:
  pytest specs/<feature>/tests/e2e/ --headed
  pytest specs/<feature>/tests/e2e/ --browser chromium
"""

from __future__ import annotations

from pathlib import Path

import pytest
from playwright.sync_api import Page, expect


# =============================================================================
# Test Data (move to fixtures/ for complex scenarios)
# =============================================================================

TEST_DATA = {
    "valid_user": {
        "email": "test@example.com",
        "password": "testPassword123",
    },
    # Add more test data as needed
}


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(scope="function")
def authenticated_page(page: Page) -> Page:
    """Fixture: Pre-authenticated page for tests requiring login.

    Usage:
        def test_dashboard(authenticated_page):
            authenticated_page.goto("/dashboard")
    """
    page.goto("/login")
    page.fill('input[name="email"]', TEST_DATA["valid_user"]["email"])
    page.fill('input[name="password"]', TEST_DATA["valid_user"]["password"])
    page.click('button[type="submit"]')
    # Wait for login to complete
    page.wait_for_url("**/dashboard**")
    return page


# =============================================================================
# Test Class: FEAT-EDISHIPMENTREPORTIMPORT - <Feature Name>
# =============================================================================

class TestFeatureXXX:
    """E2E tests for FEAT-EDISHIPMENTREPORTIMPORT: <Feature Name>

    Test IDs follow plan.md: TS-E2E-01, TS-E2E-02, ...
    """

    def test_e2e_01_initial_page_load(self, page: Page) -> None:
        """TS-E2E-01: Initial page loads correctly.

        @ac AC-US-EDISHIPMENTREPORTIMPORT-001-01 - <AC Statement>

        Given: User navigates to the application
        When: The page loads
        Then: The main heading is visible
        """
        # Arrange
        page.goto("/")

        # Act - page loads automatically

        # Assert
        expect(page.locator("h1")).to_be_visible()
        expect(page).to_have_title("Expected Title")

    def test_e2e_02_user_login_flow(self, page: Page) -> None:
        """TS-E2E-02: User can log in successfully.

        @ac AC-US-EDISHIPMENTREPORTIMPORT-001-02 - <AC Statement>

        Given: User is on the login page
        When: User enters valid credentials and submits
        Then: User is redirected to dashboard
        """
        # Arrange
        page.goto("/login")

        # Act
        page.fill('input[name="email"]', TEST_DATA["valid_user"]["email"])
        page.fill('input[name="password"]', TEST_DATA["valid_user"]["password"])
        page.click('button[type="submit"]')

        # Assert
        page.wait_for_url("**/dashboard**")
        expect(page.locator('[data-testid="welcome-message"]')).to_be_visible()

    def test_e2e_03_protected_route_requires_auth(self, page: Page) -> None:
        """TS-E2E-03: Protected routes redirect unauthenticated users.

        @ac AC-US-EDISHIPMENTREPORTIMPORT-001-03 - <AC Statement>

        Given: User is not logged in
        When: User tries to access a protected route
        Then: User is redirected to login page
        """
        # Arrange - ensure not logged in (fresh page)

        # Act
        page.goto("/dashboard")

        # Assert
        page.wait_for_url("**/login**")
        expect(page.locator('input[name="email"]')).to_be_visible()

    def test_e2e_04_example_with_authenticated_user(
        self, authenticated_page: Page
    ) -> None:
        """TS-E2E-04: Authenticated user can access dashboard.

        @ac AC-US-EDISHIPMENTREPORTIMPORT-002-01 - <AC Statement>

        Given: User is logged in
        When: User navigates to dashboard
        Then: Dashboard content is displayed
        """
        # Arrange - authenticated_page fixture handles login

        # Act
        authenticated_page.goto("/dashboard")

        # Assert
        expect(authenticated_page.locator('[data-testid="dashboard"]')).to_be_visible()


# =============================================================================
# Workflow Tests (Complete User Journey)
# =============================================================================

class TestCompleteWorkflow:
    """End-to-end workflow tests covering full user journeys.

    These tests cover critical paths that span multiple features.
    """

    def test_complete_order_workflow(self, page: Page) -> None:
        """TS-E2E-10: Complete order workflow from creation to completion.

        @ac AC-US-EDISHIPMENTREPORTIMPORT-010-01 - Complete workflow

        This test covers:
        1. User login
        2. Order creation
        3. Order confirmation
        4. Order completion
        5. History verification
        """
        # Step 1: Login
        page.goto("/login")
        page.fill('input[name="email"]', TEST_DATA["valid_user"]["email"])
        page.fill('input[name="password"]', TEST_DATA["valid_user"]["password"])
        page.click('button[type="submit"]')
        page.wait_for_url("**/dashboard**")

        # Step 2: Create order
        page.click('[data-testid="create-order-btn"]')
        page.fill('input[name="item"]', "Test Item")
        page.fill('input[name="quantity"]', "10")
        page.click('button[type="submit"]')

        # Step 3: Verify order created
        expect(page.locator('[data-testid="success-message"]')).to_be_visible()

        # Step 4: Check order in list
        page.goto("/orders")
        expect(page.locator('text=Test Item')).to_be_visible()

        # Step 5: Verify in history
        page.goto("/history")
        expect(page.locator('text=Test Item')).to_be_visible()


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestErrorScenarios:
    """E2E tests for error handling scenarios."""

    def test_invalid_login_shows_error(self, page: Page) -> None:
        """TS-E2E-20: Invalid credentials show error message.

        @ac AC-US-EDISHIPMENTREPORTIMPORT-020-01 - Error handling
        """
        page.goto("/login")
        page.fill('input[name="email"]', "invalid@example.com")
        page.fill('input[name="password"]', "wrongpassword")
        page.click('button[type="submit"]')

        expect(page.locator('[data-testid="error-message"]')).to_be_visible()
        expect(page.locator('[data-testid="error-message"]')).to_contain_text(
            "Invalid credentials"
        )

    def test_form_validation_errors(self, page: Page) -> None:
        """TS-E2E-21: Form validation errors are displayed.

        @ac AC-US-EDISHIPMENTREPORTIMPORT-020-02 - Validation
        """
        page.goto("/register")
        page.click('button[type="submit"]')  # Submit empty form

        # Check validation messages appear
        expect(page.locator('[data-testid="email-error"]')).to_be_visible()
        expect(page.locator('[data-testid="password-error"]')).to_be_visible()


# =============================================================================
# Triage Helper: Auto-capture on failure
# =============================================================================

@pytest.fixture(autouse=True)
def capture_failure_artifacts(page: Page, request: pytest.FixtureRequest):
    """Automatically capture screenshots and logs on test failure.

    This fixture runs after each test and saves diagnostics if the test failed.
    Uses Path(__file__) to resolve path relative to this file, not CWD.
    """
    # Path relative to this file: specs/<feature>/tests/e2e/ -> specs/<feature>/tests/reports/e2e/
    REPORTS_DIR = Path(__file__).parent.parent / "reports" / "e2e"

    yield  # Test runs here

    # After test: check if failed
    if request.node.rep_call and request.node.rep_call.failed:
        # Ensure directory exists
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)

        # Save screenshot
        screenshot_path = REPORTS_DIR / f"{request.node.name}.png"
        page.screenshot(path=str(screenshot_path), full_page=True)

        # Save page content
        html_path = REPORTS_DIR / f"{request.node.name}.html"
        with open(html_path, "w") as f:
            f.write(page.content())

        print(f"\n📸 Failure artifacts saved to: {REPORTS_DIR}")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook to store test result on the request node."""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)
