from __future__ import annotations

from datetime import date

from sqlalchemy import and_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models.daily_metric import DailyMetric


class MetricRepository:
    """Daily metrics access with upsert-based dedupe (newest upload wins)."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def upsert_many(self, rows: list[dict], upload_id: str) -> int:
        """Insert metrics, overwriting existing (date, metric, source) rows.

        Uses PostgreSQL ON CONFLICT so the newest upload wins atomically.
        Returns the number of rows written.
        """
        if not rows:
            return 0
        for r in rows:
            r["upload_id"] = upload_id
        if self.db.bind.dialect.name == "sqlite":
            for r in rows:
                existing = self.db.scalar(
                    select(DailyMetric).where(
                        and_(
                            DailyMetric.metric_date == r["metric_date"],
                            DailyMetric.metric == r["metric"],
                            DailyMetric.source == r["source"]
                        )
                    )
                )
                if existing:
                    existing.value = r["value"]
                    existing.upload_id = upload_id
                else:
                    self.db.add(DailyMetric(**r))
            self.db.flush()
            return len(rows)
        stmt = pg_insert(DailyMetric).values(rows)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_daily_metric",
            set_={"value": stmt.excluded.value, "upload_id": stmt.excluded.upload_id},
        )
        self.db.execute(stmt)
        return len(rows)

    def range(
        self, source: str | None, metric: str | None, start: date, end: date
    ) -> list[DailyMetric]:
        conds = [DailyMetric.metric_date >= start, DailyMetric.metric_date <= end]
        if source:
            conds.append(DailyMetric.source == source)
        if metric:
            conds.append(DailyMetric.metric == metric)
        return list(
            self.db.scalars(
                select(DailyMetric).where(and_(*conds)).order_by(DailyMetric.metric_date)
            )
        )

    def earliest_date(self) -> date | None:
        return self.db.scalar(select(DailyMetric.metric_date).order_by(DailyMetric.metric_date).limit(1))

    def latest_date(self) -> date | None:
        return self.db.scalar(
            select(DailyMetric.metric_date).order_by(DailyMetric.metric_date.desc()).limit(1)
        )
