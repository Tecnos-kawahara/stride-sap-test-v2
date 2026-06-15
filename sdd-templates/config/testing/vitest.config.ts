/// <reference types="vitest" />
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

/**
 * SDD Template - Vitest Configuration
 * Version: 5.3.3-tecnos-stride
 *
 * Usage:
 *   1. Copy to project root
 *   2. Update FEATURE_NAME placeholder
 *   3. Adjust paths as needed
 */

// TODO: Replace with actual feature name
const FEATURE_NAME = 'XXX_feature_name'

export default defineConfig({
  plugins: [react()],

  test: {
    // Test environment
    environment: 'jsdom',

    // Global test setup
    globals: true,
    setupFiles: [`./specs/${FEATURE_NAME}/tests/setup.ts`],

    // Test file patterns
    include: [
      `specs/${FEATURE_NAME}/tests/unit/**/*.{test,spec}.{ts,tsx}`,
      `specs/${FEATURE_NAME}/tests/integration/**/*.{test,spec}.{ts,tsx}`,
    ],
    exclude: [
      '**/node_modules/**',
      '**/e2e/**',  // E2E tests use Playwright
    ],

    // Coverage configuration (Layer-3: Code Coverage)
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      reportsDirectory: `./specs/${FEATURE_NAME}/tests/reports/coverage`,

      // Coverage thresholds (from plan.md)
      thresholds: {
        lines: 80,
        branches: 70,
        functions: 80,
        statements: 80,
      },

      // Include/exclude patterns
      include: ['src/**/*.{ts,tsx}'],
      exclude: [
        '**/node_modules/**',
        '**/*.d.ts',
        '**/generated/**',
        '**/*.config.{ts,js}',
        '**/tests/**',
      ],
    },

    // Reporter configuration
    reporters: ['verbose', 'junit'],
    outputFile: {
      junit: `./specs/${FEATURE_NAME}/tests/reports/junit.xml`,
    },

    // Timeouts
    testTimeout: 10000,
    hookTimeout: 10000,
  },

  // Path aliases
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@tests': path.resolve(__dirname, `./specs/${FEATURE_NAME}/tests`),
    },
  },
})
