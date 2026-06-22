"""FastAPI application entrypoint."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import birdseye, copywriting, dashboard, insights, uploads
from app.core.config import get_settings
from app.core.logging import configure_logging

configure_logging()
settings = get_settings()

app = FastAPI(title=settings.app_name, debug=settings.debug)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
is_vercel = "VERCEL" in os.environ
api_prefix = "" if is_vercel else settings.api_v1_prefix

app.include_router(uploads.router, prefix=api_prefix)
app.include_router(dashboard.router, prefix=api_prefix)
app.include_router(insights.router, prefix=api_prefix)
app.include_router(birdseye.router, prefix=api_prefix)
app.include_router(copywriting.router, prefix=api_prefix)



@app.get("/health", tags=["health"])
@app.get("/api/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.on_event("startup")
def on_startup():
    from app.database.session import SessionLocal
    db = SessionLocal()
    try:
        from app.models.post import Post
        posts = db.query(Post).filter(Post.post_type == None).all()
        if posts:
            for p in posts:
                title_lower = (p.title or "").lower()
                if any(word in title_lower for word in ["pdf", "carousel", "slide", "document", "swipe"]):
                    p.post_type = "document"
                elif "http" in title_lower or "lnkd.in" in title_lower:
                    p.post_type = "link"
                else:
                    p.post_type = "text"
            db.commit()
    except Exception as exc:
        print(f"Startup backfill failed: {exc}")
    finally:
        db.close()

