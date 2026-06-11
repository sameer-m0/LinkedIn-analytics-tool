from __future__ import annotations

import enum
import uuid

from sqlalchemy import BigInteger, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class UploadType(str, enum.Enum):
    FOLLOWERS = "followers"
    VISITORS = "visitors"
    CONTENT = "content"
    UNKNOWN = "unknown"


class UploadStatus(str, enum.Enum):
    PENDING = "pending"
    PARSED = "parsed"
    DUPLICATE = "duplicate"  # identical content re-uploaded -> no-op
    FAILED = "failed"


class Upload(Base, TimestampMixin):
    """One ingested export file. ``content_hash`` enables no-op re-uploads."""

    __tablename__ = "uploads"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    upload_type: Mapped[UploadType] = mapped_column(
        Enum(UploadType, name="upload_type"), nullable=False, default=UploadType.UNKNOWN
    )
    status: Mapped[UploadStatus] = mapped_column(
        Enum(UploadStatus, name="upload_status"), nullable=False, default=UploadStatus.PENDING
    )
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    detected_format: Mapped[str | None] = mapped_column(String(16))
    rows_ingested: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # JSON-serialized validation report (warnings, detected headers, mappings).
    report: Mapped[str | None] = mapped_column(Text)
    error: Mapped[str | None] = mapped_column(Text)
