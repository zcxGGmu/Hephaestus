# Architecture

## High-Level Flow

```text
Frontend (Next.js)
  -> Backend API (FastAPI)
  -> Redis queue / pubsub
  -> Dramatiq worker
  -> Agent runtime / tools / sandbox
  -> PostgreSQL persistence
```

## Main Areas

- `frontend/`: UI, routing, auth flow, thread rendering, tool panels
- `backend/`: auth, projects, threads, agent execution, sandbox access
- `backend/services/postgresql.py`: PostgreSQL wrapper with Supabase-like query style
- `backend/services/redis.py`: queue and stream coordination
- `backend/run_agent_background.py`: worker entrypoint

## Key Runtime Pieces

- API process serves HTTP requests
- Worker process executes long-running agent tasks
- Redis coordinates async execution and streaming updates
- PostgreSQL stores users, projects, threads, messages, agent runs, and session state

