from __future__ import annotations

import os
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.database.session import get_db
from app.models.upload import UploadType
from app.schemas.upload import UploadOut, UploadResult
from app.services.ingestion import IngestionService

router = APIRouter(prefix="/uploads", tags=["uploads"])
settings = get_settings()


@router.post("", response_model=UploadResult, status_code=201)
async def create_upload(
    db: Annotated[Session, Depends(get_db)],
    file: Annotated[UploadFile, File(...)],
    override_type: Annotated[UploadType | None, Form()] = None,
) -> UploadResult:
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in settings.allowed_extensions:
        raise HTTPException(400, f"Unsupported file type '{ext}'. Allowed: {settings.allowed_extensions}")

    data = await file.read()
    if not data:
        raise HTTPException(400, "Empty file.")
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(413, "File too large.")

    service = IngestionService(db)
    upload, report, duplicate = service.ingest(
        file.filename or "upload.xlsx", data,
        override=override_type if override_type and override_type != UploadType.UNKNOWN else None,
    )
    return UploadResult(upload=UploadOut.model_validate(upload), report=report, duplicate=duplicate)


@router.get("", response_model=list[UploadOut])
def list_uploads(db: Annotated[Session, Depends(get_db)]) -> list[UploadOut]:
    from app.repositories.upload_repository import UploadRepository

    return [UploadOut.model_validate(u) for u in UploadRepository(db).list()]
