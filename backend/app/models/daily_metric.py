from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class DailyMetric(Base, TimestampMixin):
    """A single (date, metric, source) datapoint.

    Long/narrow ("tidy") shape rather than one wide column per metric. This is
    the key extensibility decision: new metrics never require a migration, and
    dedupe is a simple unique key. ``upload_id`` records provenance and which
    upload last "won" the dedupe.
    """

    __tablename__ = "daily_metrics"
    __table_args__ = (
        UniqueConstraint("metric_date", "metric", "source", name="uq_daily_metric"),
        Index("ix_daily_metrics_lookup", "source", "metric", "metric_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    metric_date: Mapped[date] = mapped_column(Date, nullable=False)
    # source = which export produced it: followers | visitors | content
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    # metric key, e.g. organic_followers, page_views, impressions, engagement_rate
    metric: Mapped[str] = mapped_column(String(64), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)

    upload_id: Mapped[str] = mapped_column(ForeignKey("uploads.id", ondelete="SET NULL"), nullable=True)
