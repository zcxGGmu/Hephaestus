# Development

## Recommended Workflow

1. Start PostgreSQL and Redis first.
2. Run backend API and worker in separate terminals.
3. Run frontend locally with `npm run dev`.
4. Use a private `.env` and never commit real credentials.

Or use the root helper scripts:

- `scripts/check-prereqs.ps1`
- `scripts/init-backend.ps1`
- `scripts/dev-all.ps1`

## Repository Conventions

- Keep backend-only config in `backend/.env`
- Keep frontend-only config in `frontend/.env.local`
- Put cross-cutting documentation in `docs/`
- Put local helper scripts in `scripts/`
- Keep build outputs, caches, and local secrets out of Git

## Things To Clean Up Later

- The backend still contains upstream migration traces and large vendored content.
- The frontend still includes some transitional Supabase-related code paths.
- Some course-package artifacts were normalized, but the codebase is still best treated as a migration-stage project.
- `backend/adk-python-main` is large and should eventually be reviewed as either a vendored dependency, a submodule, or an external reference.
