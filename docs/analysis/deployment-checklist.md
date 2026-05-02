# Deployment Checklist

## Goal

This checklist is for getting a minimal local Hephaestus environment running.

## Required Components

- Python 3.11
- Node.js 22 or compatible
- PostgreSQL
- Redis

## Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python scripts/01_setup_database.py
python scripts/02_setup_redis.py
python scripts/03_init_hephaestus_table.py
```

Start the backend API:

```powershell
python api.py
```

Start the background worker:

```powershell
dramatiq run_agent_background
```

## Frontend

```powershell
cd frontend
Copy-Item env.example .env.local
npm install
npm run dev
```

## Website

The public website is static and lives in:

```text
website/
```

It is deployed through GitHub Pages using:

```text
.github/workflows/deploy-website.yml
```

## Common Problems

### Backend does not start

Check:

- Python environment activation
- missing environment variables
- PostgreSQL reachability
- Redis reachability

### Frontend build fails

Check:

- `npm install` completed successfully
- `NEXT_PUBLIC_BACKEND_URL` is configured
- the backend is actually running

### Website does not update

Check:

- GitHub Pages is configured to use GitHub Actions
- the workflow `Deploy Website` completed successfully
- the website URL includes the repository path:
  `https://zcxggmu.github.io/Hephaestus/`

