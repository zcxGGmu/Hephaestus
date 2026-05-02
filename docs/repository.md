# Repository Structure

## Current Shape

This repository has been normalized into a simple monorepo:

```text
Hephaestus/
  backend/
  frontend/
  docs/
  scripts/
```

## Core Working Directories

- `backend/`
  Main Python application code, API entrypoints, worker entrypoint, migrations, auth, agent logic, sandbox logic.

- `frontend/`
  Main Next.js application, thread UI, tool rendering, dashboard, auth pages, frontend API wrappers.

- `docs/`
  Cross-cutting project docs that explain setup, architecture, workflow, and repo decisions.

- `scripts/`
  Root-level PowerShell helper scripts for local development on Windows.

## Notable Heavy or Transitional Areas

- `backend/adk-python-main/`
  Large upstream ADK-related content currently checked in with the backend tree.
  This is useful for study and compatibility, but it makes the repository heavier than a typical app repo.

- `backend/supabase/`
  Migration-stage compatibility content retained from the upstream architecture.

- `frontend/src/lib/supabase/`
  Transitional frontend code paths still present while the app moves toward a custom auth/backend-first shape.

## Future Cleanup Candidates

1. Decide whether `backend/adk-python-main/` should stay vendored in-repo.
2. Reduce or isolate upstream compatibility layers that are no longer used.
3. Add shared root tooling for linting, checks, and local orchestration.
4. Consider a future `apps/` and `packages/` split if the repository grows further.

