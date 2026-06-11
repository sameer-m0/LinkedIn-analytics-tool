from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class Post(Base, TimestampMixin):
    """A published piece of content. Deduped by ``post_url`` (newest wins)."""

    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    post_url: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True, index=True)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    post_type: Mapped[str | None] = mapped_column(String(64))  # image, video, article, text, ...
    title: Mapped[str | None] = mapped_column(Text)

    impressions: Mapped[int] = mapped_column(Integer, default=0)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    reactions: Mapped[int] = mapped_column(Integer, default=0)
    comments: Mapped[int] = mapped_column(Integer, default=0)
    reposts: Mapped[int] = mapped_column(Integer, default=0)
    # Stored as a fraction (0.05 == 5%). Derived if not present in the export.
    engagement_rate: Mapped[float | None] = mapped_column(Float)
    ctr: Mapped[float | None] = mapped_column(Float)

    upload_id: Mapped[str] = mapped_column(ForeignKey("uploads.id", ondelete="SET NULL"), nullable=True)
