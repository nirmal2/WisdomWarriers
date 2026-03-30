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
- **Backend** → Render (Web Service, `uvicorn backend.main:app --host 0.0.0.0`)
- **Frontend** → Vercel (`npm run build`, output `dist/`)
- **Database** → Supabase (enable pgvector extension)
