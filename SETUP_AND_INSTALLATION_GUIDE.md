# Setup & Installation Guide

This guide explains how to install and run the full project (FastAPI backend + Celery worker + Next.js frontend).

## 1. Prerequisites

Install these first:

- Python 3.11+ (recommended)
- Node.js 20+
- npm
- Redis server (local or remote)
- Git

## 2. Clone and open project

```powershell
git clone <your-repo-url>
cd "g:\new gg"
```

## 3. Python environment and backend dependencies

Create and activate virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install backend packages:

```powershell
pip install --upgrade pip
pip install fastapi uvicorn python-dotenv sqlalchemy asyncpg celery redis requests python-jose[cryptography] passlib[bcrypt] python-multipart reportlab jira PyGithub rank-bm25
```

## 4. Frontend dependencies

Install Node packages:

```powershell
npm install
```

## 5. Environment variables

Create a `.env` file in the project root with at least the following keys:

```env
# Required core services
DATABASE_URL=postgresql://<user>:<password>@<host>:5432/<db>
REDIS_URL=redis://localhost:6379

# Auth
JWT_SECRET_KEY=replace_with_long_random_secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# GitHub webhook validation
GITHUB_WEBHOOK_SECRET=replace_with_webhook_secret

# GitHub API (one token or many)
GITHUB_TOKEN=ghp_xxx
# OR
# GITHUB_TOKENS=ghp_xxx,ghp_yyy

# Jira integration
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=you@company.com
JIRA_API_TOKEN=jira_api_token

# Optional health/alerts
SLACK_WEBHOOK_URL=
MIN_WORKERS=4
```

Notes:
- `DATABASE_URL` can be `postgres://...` or `postgresql://...`; app normalizes it for async SQLAlchemy.
- Keep `.env` out of git.

## 6. Start Redis

If Redis is installed locally as a service, ensure it is running.

If using Docker:

```powershell
docker run --name dev-redis -p 6379:6379 -d redis:7
```

## 7. Run backend API (FastAPI)

In terminal 1:

```powershell
cd "g:\new gg"
.\.venv\Scripts\Activate.ps1
python -m uvicorn main:app --reload --port 8000
```

Health endpoint:
- http://localhost:8000/health

## 8. Run Celery worker

In terminal 2:

```powershell
cd "g:\new gg"
.\.venv\Scripts\Activate.ps1
$env:REDIS_URL="redis://localhost:6379"
python -m celery -A celery_app worker --pool=solo --loglevel=info
```

Optional (periodic health checks): run Celery beat in terminal 3:

```powershell
cd "g:\new gg"
.\.venv\Scripts\Activate.ps1
$env:REDIS_URL="redis://localhost:6379"
python -m celery -A celery_app beat --loglevel=info
```

## 9. Run frontend (Next.js)

In terminal 4:

```powershell
cd "g:\new gg"
npm run dev
```

Frontend URL:
- http://localhost:3000

## 10. Webhook setup (GitHub)

1. In GitHub repo settings, create a webhook:
- Payload URL: `http://<your-public-url>/webhook/github`
- Content type: `application/json`
- Secret: same value as `GITHUB_WEBHOOK_SECRET`
- Event: push events

2. Expose local backend to internet (one option):

```powershell
npx ngrok http 8000
```

3. Use ngrok URL in webhook payload URL, then push a commit.

Expected backend response path:
- POST `/webhook/github` queues `process_commit` Celery task.

## 11. Quick verification checklist

- Backend running: `GET /health` returns `{ "status": "ok" ... }`
- Celery worker logs show worker connected to Redis
- Frontend loads on port 3000
- GitHub webhook delivery shows HTTP 200
- Celery logs show `process_commit` task execution

## 12. Common issues

- Missing env var error:
  - Check `.env` exists and includes required keys.
- Redis connection failures:
  - Confirm `REDIS_URL` and Redis service availability.
- DB connection timeout:
  - Validate `DATABASE_URL` and network access to Postgres.
- Frontend `npm run dev` fails:
  - Delete `.next` and retry: `Remove-Item -Recurse -Force .next` then `npm run dev`.
