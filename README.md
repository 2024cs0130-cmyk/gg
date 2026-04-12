# 🚀 DevPulse - Real-time Developer Analytics & Tracking

Welcome to **DevPulse**, an advanced developer productivity and analytics platform. This application integrates seamlessly with GitHub and Jira to process source code commits, extract ticket information, and perform real-time tracking of organizational health scores.

## 🌟 Key Features

- **Real-Time Data Processing:** Receives GitHub webhook payloads and processes commits instantly using Celery workers.
- **Smart Insights:** Extracts Jira ticket IDs and tracks modified files across repositories.
- **Live Score Streaming:** Utilizes WebSockets to stream real-time organizational productivity and health scores directly to the frontend.
- **Secure Authentication:** Robust role-based access using JWTs, bcrypt hashing, and SQLAlchemy ORM models.
- **Scalable Architecture:** A clear separation of concerns with a Next.js (React) frontend and a high-performance FastAPI back-end.

## 🛠️ Technology Stack

- **Frontend:** Next.js (TypeScript), Tailwind CSS.
- **Backend API:** FastAPI (Async Python, Uvicorn).
- **Database:** PostgreSQL (Asyncpg, SQLAlchemy).
- **Task Queue & Caching:** Celery, Redis.
- **Integration:** PyGithub, Jira API, Rank-BM25.

---

## 🏗️ Project Structure

The repository is modularized into two distinct applications:

1. `frontend/` - Contains the Next.js UI, styles, and configurations.
2. `backend/` - Contains the FastAPI application, database schemas, and background worker systems.

---

## ⚡ Getting Started (Local Development)

### Prerequisites

- Python 3.11+
- Node.js 20+ and npm
- PostgreSQL database
- Redis Server (local or via Docker)

### 1. Database & Cache Setup

Ensure your PostgreSQL and Redis services are up and running. If using Docker for Redis:
```bash
docker run --name devpulse-redis -p 6379:6379 -d redis:7
```

### 2. Backend Setup & Run

Open a terminal and navigate to the backend directory:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Or `.\.venv\Scripts\Activate.ps1` on Windows
pip install -r requirements.txt
```

Create a `.env` file in the `backend/` folder based on `.env.example` configurations (including `DATABASE_URL`, `REDIS_URL`, `GITHUB_WEBHOOK_SECRET`, etc.).

**Run the API Server:**
```bash
python -m uvicorn main:app --reload --port 8000
```
Health Endpoint: `http://localhost:8000/health`

**Run the Celery Worker (In a separate terminal):**
```bash
cd backend
source .venv/bin/activate
export REDIS_URL="redis://localhost:6379"  # Use \$env:REDIS_URL on Windows
python -m celery -A celery_app worker --pool=solo --loglevel=info
```

### 3. Frontend Setup & Run

Open another terminal and navigate to the frontend directory:

```bash
cd frontend
npm install
npm run dev
```
Frontend URL: `http://localhost:3000`

---

## 🪝 Configuring GitHub Webhooks

1. Go to your GitHub repository > Settings > Webhooks > Add Webhook.
2. Set the **Payload URL** to `http://<your-public-url>/webhook/github` (use `ngrok` for local testing).
3. Set **Content type** to `application/json`.
4. Enter the same secret as `GITHUB_WEBHOOK_SECRET` in your backend environment.
5. Select "Just the push event" and save.

## 🤝 Contributing & License

Contributions are always welcome. Please follow standard pull request workflows to submit code changes.

*(Note: Add your specific license details here depending on your project's privacy)*
