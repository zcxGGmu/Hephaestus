# Hephaestus

Hephaestus is a consolidated monorepo for the extracted `FuFanManus` Part 1 full-stack source code.

## Repository Layout

```text
Hephaestus/
  backend/   FastAPI + PostgreSQL + Redis + Dramatiq + ADK
  frontend/  Next.js 15 + React 18 application
  docs/      Project docs, setup notes, architecture notes
  scripts/   Local development helper scripts
```

## Quick Start

1. Read [docs/setup.md](docs/setup.md).
2. Copy [`.env.example`](.env.example) and fill your local values.
3. Initialize the backend environment and database.
4. Start backend API and worker.
5. Start the frontend app.

## Local Development

- Backend source: [backend](backend)
- Frontend source: [frontend](frontend)
- Setup guide: [docs/setup.md](docs/setup.md)
- Architecture notes: [docs/architecture.md](docs/architecture.md)
- Development conventions: [docs/development.md](docs/development.md)
- Repository structure notes: [docs/repository.md](docs/repository.md)

## Helper Scripts

- `scripts/check-prereqs.ps1`
- `scripts/init-backend.ps1`
- `scripts/dev-backend.ps1`
- `scripts/dev-worker.ps1`
- `scripts/dev-frontend.ps1`
- `scripts/dev-all.ps1`

These scripts are PowerShell helpers for local Windows development.

## Notes

- This repository was normalized from a course package and still contains upstream migration traces.
- Sample secrets have been replaced with placeholders.
- Build outputs and local env files should stay out of version control.
