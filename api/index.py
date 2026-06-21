import os
import sys

# ---------------------------------------------------------------------------
# 1. Make the ``backend/`` package importable from the repo root.
# ---------------------------------------------------------------------------
_backend_dir = os.path.join(os.path.dirname(__file__), "..", "backend")
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

# ---------------------------------------------------------------------------
# 2. Normalise DATABASE_URL for SQLAlchemy + psycopg3.
# ---------------------------------------------------------------------------
_db_url = os.environ.get("DATABASE_URL", "")
if _db_url.startswith("postgresql://"):
    os.environ["DATABASE_URL"] = _db_url.replace(
        "postgresql://", "postgresql+psycopg://", 1
    )
elif _db_url.startswith("postgres://"):
    os.environ["DATABASE_URL"] = _db_url.replace(
        "postgres://", "postgresql+psycopg://", 1
    )

# ---------------------------------------------------------------------------
# 3. Import the FastAPI app at top-level scope for Vercel static analyzer.
# ---------------------------------------------------------------------------
from app.main import app  # noqa: E402

# ---------------------------------------------------------------------------
# 4. Use FastAPI startup event to initialize database tables.
# ---------------------------------------------------------------------------
@app.on_event("startup")
def on_startup():
    print("Vercel startup event: Initializing database...", flush=True)
    try:
        from app.database.base import Base
        from app.database.session import engine
        
        # Force-import every model so Base.metadata knows about them.
        import app.models.upload  # noqa: F401
        import app.models.daily_metric  # noqa: F401
        import app.models.post  # noqa: F401
        import app.models.demographic  # noqa: F401
        
        Base.metadata.create_all(bind=engine)
        print("Vercel startup event: Database initialization complete.", flush=True)
    except Exception as e:
        import traceback
        print("!!! ERROR DURING DATABASE INITIALIZATION !!!", file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)
        # We don't re-raise here so the app container doesn't immediately crash.
        # This allows endpoints (like /api/health) to load and report status,
        # making debugging much easier.
