# Setup

## Prerequisites

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
python scripts/03_init_fufanmanus_table.py
```

Start the API:

```powershell
python api.py
```

Start the worker in a second terminal:

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

Frontend default URL:

```text
http://localhost:3000
```

## Minimum Environment Values

Backend:

- `DATABASE_URL`
- `REDIS_HOST`
- `REDIS_PORT`
- `JWT_SECRET_KEY`
- one working model key such as `OPENAI_API_KEY` or `DEEPSEEK_API_KEY`

Frontend:

- `NEXT_PUBLIC_BACKEND_URL`
- `NEXT_PUBLIC_URL`
- `NEXT_PUBLIC_ENV_MODE`

