/**
 * E2E Test Template
 *
 * Template Version: {{TEMPLATE_VERSION}}
 * Feature: FEAT-XXX
 *
 * This template provides a structure for E2E tests following the SDD workflow.
 * Each test should map to an AC with the 'e2e' tag in spec.md.
 *
 * Naming Convention:
 *   - File: test_<scenario>.spec.ts (e.g., test_order_flow.spec.ts)
 *   - Test ID: TS-E2E-NN (matches plan.md test IDs)
 *
 * AC Coverage:
 *   - Add @ac:AC-US-FEATXXX-001-01 in test description to link to ACs
 *   - This enables traceability from test to spec
 */

import { test, expect } from '@playwright/test';

// Test data (consider moving to fixtures for complex scenarios)
const testData = {
  validUser: {
    email: 'test@example.com',
    password: 'testPassword123',
  },
  // Add more test data as needed
};

test.describe('FEAT-XXX: <Feature Name>', () => {
  test.beforeEach(async ({ page }) => {
    // Setup: Navigate to the starting page
    await page.goto('/');

    // Additional setup (login, accept cookies, etc.)
  });

  test.afterEach(async ({ page }) => {
    // Cleanup: Reset state if needed
  });

  /**
   * TS-E2E-01: <Test Title>
   * @ac AC-US-FEATXXX-001-01 - <AC Statement>
   *
   * Given: <Precondition>
   * When: <Action>
   * Then: <Expected Result>
   */
  test('TS-E2E-01: <test description matching AC>', async ({ page }) => {
    // Arrange
    // ...

    // Act
    // await page.click('button[data-testid="submit"]');

    // Assert
    // await expect(page.locator('h1')).toContainText('Success');
  });

  /**
   * TS-E2E-02: <Test Title>
   * @ac AC-US-FEATXXX-001-02 - <AC Statement>
   */
  test('TS-E2E-02: <test description>', async ({ page }) => {
    // Implement test
  });

  // Add more tests as defined in plan.md
});

// Triage helper: Run this to capture failure context
test.afterEach(async ({ page }, testInfo) => {
  if (testInfo.status !== 'passed') {
    // Capture additional diagnostics on failure
    const screenshot = await page.screenshot({ fullPage: true });
    await testInfo.attach('failure-screenshot', {
      body: screenshot,
      contentType: 'image/png',
    });

    // Capture console logs
    const consoleLogs: string[] = [];
    page.on('console', (msg) => consoleLogs.push(`${msg.type()}: ${msg.text()}`));
    if (consoleLogs.length > 0) {
      await testInfo.attach('console-logs', {
        body: consoleLogs.join('\n'),
        contentType: 'text/plain',
      });
    }
  }
});
