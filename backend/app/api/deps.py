"""Shared API dependencies: date-range query parsing."""

from datetime import date
from typing import Annotated

from fastapi import Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dates import ComparisonMode, DateRange, RangePreset
from app.database.session import get_db
from app.services.dashboard import DashboardService


def get_dashboard_service(db: Annotated[Session, Depends(get_db)]) -> DashboardService:
    return DashboardService(db)


class RangeParams:
    """Resolved date range + comparison mode derived from query params.

    ``today`` defaults to the latest date present in the data so presets like
    "last 30 days" make sense for historical exports rather than wall-clock now.
    """

    def __init__(
        self,
        preset: Annotated[RangePreset, Query()] = RangePreset.LAST_30,
        start: Annotated[date | None, Query()] = None,
        end: Annotated[date | None, Query()] = None,
        compare: Annotated[ComparisonMode, Query()] = ComparisonMode.PREVIOUS_PERIOD,
        db: Session = Depends(get_db),
    ) -> None:
        self.preset = preset
        self.compare = compare
        svc = DashboardService(db)
        anchor = svc.metrics.latest_date() or date.today()
        try:
            self.range: DateRange = svc.resolve(preset, anchor, start, end)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
