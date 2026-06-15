/**
 * Playwright E2E Test Configuration Template
 *
 * Template Version: {{TEMPLATE_VERSION}}
 *
 * This template provides a starting point for E2E tests using Playwright.
 * Replace FEAT-XXX with your feature ID and adjust settings as needed.
 *
 * Usage:
 *   1. Copy to specs/<feature>/tests/e2e/playwright.config.ts
 *   2. Replace placeholders (FEAT-XXX, baseURL, etc.)
 *   3. Run: npx playwright test --config=specs/<feature>/tests/e2e/playwright.config.ts
 */

import { defineConfig, devices } from '@playwright/test';
import dotenv from 'dotenv';

// Load environment variables from .env file
dotenv.config();

export default defineConfig({
  // Test directory (relative to this config file)
  testDir: './',

  // Test file pattern
  testMatch: '**/*.spec.ts',

  // Test timeout (adjust based on your application's response time)
  timeout: 60 * 1000, // 60 seconds per test

  // Expect timeout for assertions
  expect: {
    timeout: 10 * 1000, // 10 seconds
  },

  // Fail the build on CI if you accidentally left test.only in the source code
  forbidOnly: !!process.env.CI,

  // Retry configuration
  retries: process.env.CI ? 2 : 0,

  // Number of workers (parallel test execution)
  workers: process.env.CI ? 1 : undefined,

  // Reporter configuration
  // NOTE: Output to tests/reports/e2e/ (relative to specs/<feature>/tests/e2e/)
  reporter: [
    ['html', { outputFolder: '../reports/e2e/playwright-report' }],
    ['json', { outputFile: '../reports/e2e/test-results.json' }],
    ['list'],
  ],

  // Shared settings for all projects
  use: {
    // Base URL for your application
    baseURL: process.env.BASE_URL || 'http://localhost:3000',

    // Collect trace on first retry
    trace: 'on-first-retry',

    // Capture screenshot on failure
    screenshot: 'only-on-failure',

    // Record video on failure
    video: 'on-first-retry',

    // Action timeout
    actionTimeout: 15 * 1000,

    // Navigation timeout
    navigationTimeout: 30 * 1000,
  },

  // Configure projects for different browsers
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    // Uncomment to add more browsers
    // {
    //   name: 'firefox',
    //   use: { ...devices['Desktop Firefox'] },
    // },
    // {
    //   name: 'webkit',
    //   use: { ...devices['Desktop Safari'] },
    // },
  ],

  // Local dev server configuration (optional)
  // Uncomment and configure if you want Playwright to start your app
  // webServer: {
  //   command: 'npm run dev',
  //   url: 'http://localhost:3000',
  //   reuseExistingServer: !process.env.CI,
  //   timeout: 120 * 1000,
  // },

  // Output directory for test artifacts (relative to specs/<feature>/tests/e2e/)
  outputDir: '../reports/e2e/test-artifacts',
});
