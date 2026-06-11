from __future__ import annotations

from datetime import date, datetime, time

from sqlalchemy import and_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models.post import Post


class PostRepository:
    """Posts access; deduped by ``post_url`` (newest upload wins)."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def upsert_many(self, rows: list[dict], upload_id: str) -> int:
        if not rows:
            return 0
        for r in rows:
            r["upload_id"] = upload_id
        stmt = pg_insert(Post).values(rows)
        update_cols = {
            c: getattr(stmt.excluded, c)
            for c in (
                "posted_at", "post_type", "title", "impressions", "clicks",
                "reactions", "comments", "reposts", "engagement_rate", "ctr",
                "upload_id",
            )
        }
        stmt = stmt.on_conflict_do_update(index_elements=[Post.post_url], set_=update_cols)
        self.db.execute(stmt)
        return len(rows)

    def range(self, start: date, end: date) -> list[Post]:
        start_dt = datetime.combine(start, time.min)
        end_dt = datetime.combine(end, time.max)
        return list(
            self.db.scalars(
                select(Post)
                .where(and_(Post.posted_at >= start_dt, Post.posted_at <= end_dt))
                .order_by(Post.posted_at)
            )
        )

    def all(self) -> list[Post]:
        return list(self.db.scalars(select(Post).order_by(Post.posted_at)))
