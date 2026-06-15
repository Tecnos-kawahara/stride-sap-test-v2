// Monorepo Vitest Workspace Configuration
// Auto-discovers test configs across all packages
//
// Usage: Place at project root alongside turbo.json
// Ref: https://vitest.dev/guide/workspace

import { defineWorkspace } from "vitest/config";

export default defineWorkspace([
  // Auto-discover all packages with vitest config
  "packages/*/vitest.config.{ts,js}",
  "libs/*/vitest.config.{ts,js}",
  "services/*/vitest.config.{ts,js}",
  "apps/*/vitest.config.{ts,js}",
  // Add as needed:
  // "connectors/*/vitest.config.{ts,js}",
  // "specs/*/tests/contract/vitest.config.{ts,js}",
]);
