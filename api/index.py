"""Vercel serverless function entry point.

Vercel's Python runtime detects the ``app`` variable (a FastAPI/ASGI instance)
and wraps it automatically.  On every cold-start we ensure the database tables
exist so there is no need for a separate migration step.
"""
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
#    Neon gives ``postgresql://…`` but SQLAlchemy needs the driver suffix.
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
# 3. Import the FastAPI app – Vercel picks up the ``app`` name.
# ---------------------------------------------------------------------------
from app.main import app  # noqa: E402

# ---------------------------------------------------------------------------
# 4. Ensure all ORM models are loaded, then create tables on cold-start.
# ---------------------------------------------------------------------------
from app.database.base import Base  # noqa: E402
from app.database.session import engine  # noqa: E402

# Force-import every model so Base.metadata knows about them.
import app.models.upload  # noqa: F401, E402
import app.models.daily_metric  # noqa: F401, E402
import app.models.post  # noqa: F401, E402
import app.models.demographic  # noqa: F401, E402

Base.metadata.create_all(bind=engine)
