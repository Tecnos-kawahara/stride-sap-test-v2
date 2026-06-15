# Monorepo Configuration (Turborepo) — Scale Levels

> Monorepo is the DEFAULT for all SDD projects.
> Scale level determines the complexity of the setup.
> Enterprise Hierarchy (`sdd-templates/config/enterprise.yaml`) is a separate toggle from `--scale enterprise`.

## Scale Levels

| Scale | Target | Config |
|-------|--------|--------|
| **starter** (default) | Small / first-time SDD | turbo.json (build+test), tsconfig.base.json, simple CI |
| **standard** | Multi-service | Full Turborepo + vitest.workspace.ts + differential CI |
| **enterprise** | CBP-class | Standard + remote cache + full CI differential + Evidence Pack (90d) |

## Usage

```bash
stride init my_feature                     # → Starter (default)
stride init my_feature --scale standard    # → Standard
stride init my_feature --scale enterprise  # → Enterprise
```

Even Starter gets turbo.json + workspaces — a natural growth path to monorepo.

## Files per Scale

| File | starter | standard | enterprise | Destination |
|------|---------|----------|------------|-------------|
| turbo.json | turbo.starter.json | turbo.standard.json | turbo.enterprise.json | Project root |
| tsconfig.base.json | Yes | Yes | Yes | Project root |
| vitest.workspace.ts | — | Yes | Yes | Project root |
| CI template | ci-starter.yml | ci-standard.yml | ci-enterprise.yml | .github/workflows/ci.yml |
| package.json (workspaces) | Yes | Yes | Yes | (inject into existing) |

## SDD-Specific Tasks by Scale

### Starter
- **build** — TypeScript compilation
- **test** — Unit tests

### Standard / Enterprise
- **lint** — ESLint per package
- **typecheck** — TypeScript compilation check
- **test** — Unit tests via Vitest
- **test:coverage** — Coverage report generation (Evidence Pack)
- **test:contract** — Contract tests against `contracts/` specs
- **build** — TypeScript compilation

### Enterprise Additional (via CI)
- Remote cache via `TURBO_TOKEN` + `TURBO_TEAM` env vars
- `fetch-depth: 0` for accurate diff detection
- Evidence Pack artifacts with 90-day retention
- Full build verification on main branch

## Directory Structure (Recommended)

```
project-root/
├── turbo.json                 ← Turborepo config (scale-specific)
├── tsconfig.base.json         ← Shared TS config
├── vitest.workspace.ts        ← Test workspace (standard+)
├── package.json               ← Workspaces definition
├── packages/                  ← Shared packages
│   └── <pkg>/
├── libs/                      ← Library packages
│   └── <lib>/
├── services/                  ← Service packages
│   └── <svc>/
├── apps/                      ← Application packages
│   └── <app>/
├── specs/                     ← SDD specifications (per feature)
│   └── <feature>/
├── sdd-templates/             ← SDD template pack
└── .github/workflows/
    └── ci.yml                 ← CI (scale-specific)
```

## Upgrading Scale

To upgrade from starter to standard:
1. Replace `turbo.json` with standard tasks (lint, typecheck, test:coverage, test:contract)
2. Add `vitest.workspace.ts` from `sdd-templates/config/monorepo/`
3. Replace `.github/workflows/ci.yml` with `sdd-templates/config/monorepo/github-actions/ci-standard.yml`

Or re-run: `stride init <feature> --scale standard` (existing files are skipped).
