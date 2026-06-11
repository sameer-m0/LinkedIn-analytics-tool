from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.upload import UploadStatus, UploadType


class ValidationReport(BaseModel):
    detected_type: UploadType
    confidence: float
    detected_format: str
    detected_headers: dict[str, list[str]] = {}
    warnings: list[str] = []
    rows_ingested: int = 0
    metrics: int = 0
    posts: int = 0
    demographics: int = 0


class UploadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    upload_type: UploadType
    status: UploadStatus
    detected_format: str | None
    rows_ingested: int
    size_bytes: int
    created_at: datetime
    error: str | None = None


class UploadResult(BaseModel):
    upload: UploadOut
    report: ValidationReport | None = None
    duplicate: bool = False
