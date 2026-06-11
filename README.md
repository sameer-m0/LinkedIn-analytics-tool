# LinkedIn Page Analytics Dashboard

Drop in your LinkedIn page exports (Followers / Visitors / Content), get a
performance dashboard and an evidence-backed "what to do next" list.

This is an internal tool: upload Excel exports, the system parses + normalizes +
stores them historically, and serves a React dashboard with period comparison
and a deterministic insights engine.

---

## Architecture

```
backend/                       FastAPI + SQLAlchemy + Pandas + Alembic
  app/
    api/         REST routers (uploads, dashboard, insights) + deps
    core/        config, logging, pure date-range math
    database/    declarative base, engine/session
    models/      uploads, daily_metrics, posts, demographic_snapshots
    parsers/     format/header detection, locale + synonym normalization, per-type parsers
    repositories/  data access + dedupe upserts (newest-wins)
    schemas/     Pydantic request/response contracts
    services/    ingestion pipeline, dashboard aggregation, insights orchestration
    insights/    config-driven deterministic rules engine
  migrations/    Alembic
  tests/         unit (parsers, rules, dates, locale) + integration (upload/dashboard)

frontend/                      React + TypeScript + Vite + Tailwind + Recharts
  src/
    pages/       Overview, Followers, Visitors, Content, Insights, Uploads
    components/  Layout, DateRangePicker, KpiCard, Sparkline, UploadDropzone, Card
    charts/      TimeSeriesChart, CategoryBarChart
    hooks/       useFetch, useRange (date-range context)
    services/    typed API client
    types/       shared API types
    utils/       formatting helpers
```

### Key design decisions

- **Tidy (long/narrow) `daily_metrics`** — `(date, metric, source, value)`. New
  metrics never require a migration, and dedupe is a single unique key.
- **Dedupe = idempotent upsert.** Daily metrics dedupe on `(date, metric,
  source)`, posts on `post_url`, demographics on `(date, dimension, category)`.
  Every row stores its `upload_id`, so "newest upload wins" is auditable.
- **Byte-identical re-uploads are no-ops** via a SHA-256 `content_hash` unique
  index on `uploads`.
- **Parsing is layered & SOLID.** Format detection (magic bytes, so an `.xls`
  disguised as `.xlsx` is handled), header detection (heuristic — headers need
  not be on row 1), locale normalization (MM/DD vs DD/MM, `1,234` vs `1.234`),
  and column-synonym resolution are each isolated and unit-tested. New export
  types are new `BaseParser` subclasses registered in `parsers/registry.py`;
  new synonyms are one-line edits.
- **Insights engine is deterministic & config-driven.** Thresholds live in
  `insights/config.py`; each `Rule` returns an `Insight` only if it can cite
  supporting metrics — *no evidence, no recommendation*. Results sort by
  `impact × confidence`.

---

## Run with Docker (recommended)

```bash
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend API + docs: http://localhost:8000/docs
- Postgres: localhost:5432 (`linkedin` / `linkedin`)

The backend container waits for Postgres, runs Alembic migrations, then serves
the API. The frontend is built and served by nginx, which proxies `/api` to the
backend.

### Try it with sample data

```bash
pip install openpyxl
python scripts/generate_sample_data.py   # writes ./sample_data/*.xlsx
```

Open http://localhost:5173 → **Uploads** → drag the three files in. Then explore
Overview / Followers / Visitors / Content / Insights.

---

## Local development (without Docker)

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# point at a local Postgres
export DATABASE_URL="postgresql+psycopg://linkedin:linkedin@localhost:5432/linkedin_analytics"
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173, proxies /api -> http://localhost:8000
```

---

## API

| Method | Path                       | Purpose                                  |
|--------|----------------------------|------------------------------------------|
| POST   | `/api/uploads`             | Upload an export (auto-detect or override) |
| GET    | `/api/uploads`             | Upload history                           |
| GET    | `/api/dashboard/overview`  | KPIs, deltas, sparklines, top post       |
| GET    | `/api/dashboard/followers` | Daily / rolling-7d / cumulative + demographics |
| GET    | `/api/dashboard/visitors`  | Page views, unique visitors, device split, ratio |
| GET    | `/api/dashboard/content`   | Time series, post table, aggregations    |
| GET    | `/api/insights`            | Evidence-backed recommendations          |

**Range query params** (dashboard + insights): `preset` (`last_7`, `last_30`,
`last_90`, `mtd`, `qtd`, `ytd`, `all_time`, `custom`), `start`, `end` (for
`custom`), `compare` (`previous_period`, `same_period_last_year`, `none`).

---

## Tests

```bash
cd backend
pytest                       # unit tests run anywhere

# integration tests need Postgres:
export TEST_DATABASE_URL="postgresql+psycopg://linkedin:linkedin@localhost:5432/linkedin_test"
pytest tests/test_integration.py
```

- **Unit:** parsers (format/header/locale/synonyms), rule engine (each rule +
  the "no evidence" guarantee), date calculations, dedupe behavior.
- **Integration:** upload workflow, content-hash no-op, newest-upload-wins,
  dashboard aggregation. These skip automatically if Postgres is unreachable.

---

## Insight rules (initial set)

| Rule | Fires when | Recommends |
|------|-----------|------------|
| 1 | A post type's engagement ≥ 1.5× avg, n ≥ 5 | Publish more of that format |
| 2 | A weekday's impressions ≥ 1.3× avg, n ≥ 4 | Post more on that day |
| 3 | Posting frequency down ≥ 30% **and** impressions declined | Restore cadence |
| 4 | Visitor traffic up **and** follower growth flat | Improve page conversion |
| 5 | One demographic segment grows ≥ 2× the median | Target content to it |
| 6 | High-reach posts have low CTR | Improve headlines/hooks |

Add a rule by subclassing `Rule`, appending it to `rules.ALL_RULES`, and adding
its threshold block to `insights/config.py`.
