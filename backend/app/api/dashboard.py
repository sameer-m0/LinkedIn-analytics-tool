from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import RangeParams, get_dashboard_service
from app.schemas.dashboard import (
    ContentResponse,
    FollowersResponse,
    OverviewResponse,
    VisitorsResponse,
)
from app.services.dashboard import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview", response_model=OverviewResponse)
def overview(
    params: Annotated[RangeParams, Depends()],
    svc: Annotated[DashboardService, Depends(get_dashboard_service)],
) -> OverviewResponse:
    return svc.overview(params.range, params.compare)


@router.get("/followers", response_model=FollowersResponse)
def followers(
    params: Annotated[RangeParams, Depends()],
    svc: Annotated[DashboardService, Depends(get_dashboard_service)],
) -> FollowersResponse:
    return svc.followers(params.range)


@router.get("/visitors", response_model=VisitorsResponse)
def visitors(
    params: Annotated[RangeParams, Depends()],
    svc: Annotated[DashboardService, Depends(get_dashboard_service)],
) -> VisitorsResponse:
    return svc.visitors(params.range)


@router.get("/content", response_model=ContentResponse)
def content(
    params: Annotated[RangeParams, Depends()],
    svc: Annotated[DashboardService, Depends(get_dashboard_service)],
) -> ContentResponse:
    return svc.content(params.range)
