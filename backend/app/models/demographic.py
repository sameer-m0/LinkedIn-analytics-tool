from __future__ import annotations

import enum
from datetime import date

from sqlalchemy import Date, Enum, Float, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class DemographicDimension(str, enum.Enum):
    JOB_FUNCTION = "job_function"
    SENIORITY = "seniority"
    INDUSTRY = "industry"
    LOCATION = "location"
    COMPANY_SIZE = "company_size"


class DemographicSnapshot(Base, TimestampMixin):
    """Follower demographic counts captured at a point in time.

    Snapshot-based so growth-rate comparisons across dimensions are possible
    (Insights Rule 5). Deduped by (snapshot_date, dimension, category).
    """

    __tablename__ = "demographic_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "snapshot_date", "dimension", "category", name="uq_demographic_snapshot"
        ),
        Index("ix_demographic_lookup", "dimension", "snapshot_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    dimension: Mapped[DemographicDimension] = mapped_column(
        Enum(DemographicDimension, name="demographic_dimension"), nullable=False
    )
    category: Mapped[str] = mapped_column(String(256), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)  # follower count

    upload_id: Mapped[str] = mapped_column(ForeignKey("uploads.id", ondelete="SET NULL"), nullable=True)
