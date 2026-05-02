# Source Map and Runtime Guide

## Repository Map

```text
Hephaestus/
  backend/
  frontend/
  website/
  docs/
  scripts/
```

## Backend Map

Important backend entrypoints and modules:

- `backend/api.py`
  Main FastAPI entrypoint.

- `backend/run_agent_background.py`
  Dramatiq worker entrypoint for background agent execution.

- `backend/services/postgresql.py`
  PostgreSQL access layer and query wrappers.

- `backend/services/redis.py`
  Redis coordination layer for queues, pub/sub, and streaming data.

- `backend/agent/`
  Agent execution, configuration, prompts, runtime helpers, and tool orchestration.

- `backend/auth/`
  Authentication and session-related behavior.

- `backend/sandbox/`
  Sandbox file and runtime interfaces.

## Frontend Map

Important frontend areas:

- `frontend/src/app/`
  Main application routing.

- `frontend/src/app/(dashboard)/`
  Product dashboard and authenticated interface.

- `frontend/src/components/thread/`
  Thread UI, chat input, message rendering, and tool panels.

- `frontend/src/lib/api.ts`
  Frontend-side API wrappers and app data access.

- `frontend/src/hooks/useAgentStream.ts`
  Streaming state handling for agent execution updates.

## Website Map

The standalone public website lives in:

- `website/index.html`
- `website/styles.css`
- `website/script.js`

This directory is intentionally static and deployable through GitHub Pages.

## Runtime Flow

The main execution flow looks like this:

1. A user sends a request from the frontend product app
2. FastAPI creates or updates thread/run state
3. The backend enqueues a task through Redis
4. A Dramatiq worker consumes the task
5. The agent runtime performs tool and sandbox actions
6. Intermediate updates are streamed back
7. Final state is persisted in PostgreSQL

## Why This Matters

This repository is not just a chat interface.
Its value comes from connecting:

- thread context
- tool execution
- background orchestration
- persistence
- product UI

into one coherent system.

