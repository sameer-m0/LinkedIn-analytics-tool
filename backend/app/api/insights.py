from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import RangeParams
from app.database.session import get_db
from app.schemas.insight import InsightsResponse
from app.services.insights_service import InsightsService

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("", response_model=InsightsResponse)
def get_insights(
    params: Annotated[RangeParams, Depends()],
    db: Annotated[Session, Depends(get_db)],
) -> InsightsResponse:
    service = InsightsService(db)
    return InsightsResponse(
        range_start=params.range.start.isoformat(),
        range_end=params.range.end.isoformat(),
        playbook=service.playbook(params.range),
        insights=service.generate(params.range, params.compare),
    )
