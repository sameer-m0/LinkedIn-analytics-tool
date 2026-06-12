from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import RangeParams
from app.database.session import get_db
from app.schemas.birdseye import BirdsEyeResponse
from app.services.birdseye_service import BirdsEyeService

router = APIRouter(prefix="/birdseye", tags=["birdseye"])


@router.get("", response_model=BirdsEyeResponse)
def birdseye(
    params: Annotated[RangeParams, Depends()],
    db: Annotated[Session, Depends(get_db)],
) -> BirdsEyeResponse:
    return BirdsEyeService(db).analyze(params.range)
