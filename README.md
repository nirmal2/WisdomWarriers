# InstaAnalytics

Instagram analytics platform — scrapes profiles and posts via Apify, stores data in PostgreSQL with pgvector, and surfaces insights through an AI-powered chat interface.

## Stack
- **Backend**: FastAPI · SQLAlchemy async · APScheduler · pgvector · OpenAI
- **Database**: PostgreSQL 16 + pgvector (Supabase or Docker)
- **Frontend**: React + TypeScript · Vite · TailwindCSS · Recharts · React Query
- **AI**: OpenAI `text-embedding-3-small` + GPT-4o-mini (function-calling + SSE streaming)

## Project Structure
```
insta-analytics/
├── backend/
│   ├── config.py          # Settings via pydantic-settings
│   ├── db/                # Async SQLAlchemy engine + session
│   ├── models/            # SQLAlchemy ORM models
│   ├── schemas/           # Pydantic request/response schemas
│   ├── repositories/      # Database query layer
│   ├── services/          # Apify, scrape, embedding, scheduler, chat
│   ├── routers/           # FastAPI route handlers
│   ├── migrations/        # Alembic migrations
│   ├── main.py
│   └── requirements.txt
└── frontend/
    └── src/
        ├── api/           # Fetch helpers
        ├── hooks/         # React Query + custom hooks
        ├── components/    # Shared UI components
        ├── pages/         # Dashboard, Profiles, Posts, Analytics, Schedules, Chat
        └── types/         # TypeScript interfaces
```

## Quick Start (Docker)

```bash
docker compose up -d
```
Backend at http://localhost:8000 · Apply migrations:
```bash
cd backend
alembic upgrade head
```
Frontend:
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173

## Local Development

### Backend
```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # fill in secrets
alembic upgrade head
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env.local  # set VITE_API_URL
npm run dev
```

## Environment Variables

See `backend/.env.example` and `frontend/.env.example`.

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL async URL (`postgresql+asyncpg://...`) |
| `APIFY_TOKEN` | Apify API token |
| `APIFY_POSTS_ACTOR_ID` | Actor ID for Instagram posts scraper |
| `APIFY_PROFILES_ACTOR_ID` | Actor ID for Instagram profiles scraper |
| `PROFILE_SCRAPE_PARALLELISM` | Max concurrent profile fetches in non-batch mode (default: `6`) |
| `OPENAI_API_KEY` | OpenAI API key |
| `VITE_API_URL` | Backend base URL for the frontend |

## Deployment

### Option A: Render Blueprint (Backend + Frontend)

This repo includes `render.yaml` for one-click provisioning on Render.

1. In Render, click **New +** → **Blueprint**.
2. Connect this GitHub repo: `https://github.com/nirmal2/WisdomWorriers`.
3. Render will create:
    - `insta-analytics-backend` (Python web service)
    - `insta-analytics-frontend` (static site)
4. Set backend env vars in Render dashboard:
    - `DATABASE_URL` (Supabase/Postgres URL; use `postgresql+asyncpg://...`)
    - `APIFY_TOKEN`
    - `OPENAI_API_KEY`
    - `CORS_ORIGINS` (must include your frontend URL)
5. Set frontend env var:
    - `VITE_API_URL` = your backend Render URL

### Option B: Render (Backend) + Vercel (Frontend)

Backend on Render:
1. Create a new **Web Service** from this repo.
2. Root directory: `backend`
3. Build command: `pip install -r requirements.txt`
4. Start command: `alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add backend env vars listed above.

Frontend on Vercel:
1. Import this repo into Vercel.
2. Set root directory to `frontend`.
3. Set `VITE_API_URL` to your backend URL.
4. Deploy.

`frontend/vercel.json` is included so React Router deep links resolve to `index.html`.

### Database Notes

- Use Supabase PostgreSQL and enable extension: `vector`
- For hosted Postgres with TLS, include `?ssl=require` in `DATABASE_URL` if needed
- `supabase_setup.sql` contains the base tables, indexes, and constraints for a fresh Supabase database
- `supabase_analytics.sql` adds analytics views, materialized views, and helper functions after the base schema is in place

### Supabase SQL Apply Order

Run these scripts in order in the Supabase SQL Editor:

1. `supabase_setup.sql`
2. `supabase_analytics.sql`

The analytics script includes:

- Base analytics views such as `post_engagement`, `profile_follower_growth`, and `account_monthly_summary`
- Materialized views for hashtag and posting-time analysis
- `refresh_analytics_views()` to rebuild materialized analytics after a scrape run
- `search_similar_posts(...)` for pgvector-based semantic post search

`refresh_analytics_views()` uses non-concurrent refresh so it can be called safely from a Postgres function or Supabase RPC. The materialized views still keep unique indexes so you can run direct concurrent refreshes manually if needed.
