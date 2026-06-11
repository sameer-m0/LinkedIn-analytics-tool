#!/usr/bin/env bash
set -e

echo "Waiting for database..."
python - <<'PY'
import os, time
import sqlalchemy as sa
url = os.environ.get("DATABASE_URL", "postgresql+psycopg://linkedin:linkedin@db:5432/linkedin_analytics")
for attempt in range(30):
    try:
        sa.create_engine(url).connect().close()
        print("Database is ready.")
        break
    except Exception as exc:
        print(f"  db not ready ({attempt+1}/30): {exc}")
        time.sleep(2)
else:
    raise SystemExit("Database never became available")
PY

echo "Running migrations..."
alembic upgrade head

echo "Starting API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
