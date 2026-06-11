from __future__ import annotations

from datetime import date

from sqlalchemy import and_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models.demographic import DemographicDimension, DemographicSnapshot


class DemographicRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def upsert_many(self, rows: list[dict], upload_id: str) -> int:
        if not rows:
            return 0
        for r in rows:
            r["upload_id"] = upload_id
        if self.db.bind.dialect.name == "sqlite":
            for r in rows:
                existing = self.db.scalar(
                    select(DemographicSnapshot).where(
                        and_(
                            DemographicSnapshot.snapshot_date == r["snapshot_date"],
                            DemographicSnapshot.dimension == r["dimension"],
                            DemographicSnapshot.category == r["category"]
                        )
                    )
                )
                if existing:
                    existing.value = r["value"]
                    existing.upload_id = upload_id
                else:
                    self.db.add(DemographicSnapshot(**r))
            self.db.flush()
            return len(rows)
        stmt = pg_insert(DemographicSnapshot).values(rows)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_demographic_snapshot",
            set_={"value": stmt.excluded.value, "upload_id": stmt.excluded.upload_id},
        )
        self.db.execute(stmt)
        return len(rows)

    def by_dimension(self, dimension: DemographicDimension) -> list[DemographicSnapshot]:
        return list(
            self.db.scalars(
                select(DemographicSnapshot)
                .where(DemographicSnapshot.dimension == dimension)
                .order_by(DemographicSnapshot.snapshot_date)
            )
        )

    def latest_snapshot_date(self, dimension: DemographicDimension) -> date | None:
        return self.db.scalar(
            select(DemographicSnapshot.snapshot_date)
            .where(DemographicSnapshot.dimension == dimension)
            .order_by(DemographicSnapshot.snapshot_date.desc())
            .limit(1)
        )
