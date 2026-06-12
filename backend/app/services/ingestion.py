"""Ingestion pipeline: hash -> parse -> persist (dedupe) -> report.

Orchestrates parsers + repositories. Re-uploading byte-identical content is a
no-op (content hashing). Each persisted row records its ``upload_id`` so the
"newest upload wins" dedupe is auditable.
"""
from __future__ import annotations

import hashlib
import json

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.upload import Upload, UploadStatus, UploadType
from app.parsers import registry
from app.parsers.base import ParseResult
from app.repositories.demographic_repository import DemographicRepository
from app.repositories.metric_repository import MetricRepository
from app.repositories.post_repository import PostRepository
from app.repositories.upload_repository import UploadRepository
from app.schemas.upload import ValidationReport

log = get_logger(__name__)


class IngestionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.uploads = UploadRepository(db)
        self.metrics = MetricRepository(db)
        self.posts = PostRepository(db)
        self.demographics = DemographicRepository(db)

    def ingest(
        self, filename: str, data: bytes, override: UploadType | None = None
    ) -> tuple[Upload, ValidationReport | None, bool]:
        content_hash = hashlib.sha256(data).hexdigest()

        existing = self.uploads.get_by_hash(content_hash)
        if existing is not None:
            log.info("Duplicate upload %s (hash %s) - no-op", filename, content_hash[:12])
            return existing, None, True

        upload = Upload(
            filename=filename,
            content_hash=content_hash,
            size_bytes=len(data),
            status=UploadStatus.PENDING,
            upload_type=override or UploadType.UNKNOWN,
        )
        self.uploads.add(upload)

        try:
            result, workbook, confidence = registry.parse(data, override=override)
        except Exception as exc:  # noqa: BLE001 - surface parse failure in report
            upload.status = UploadStatus.FAILED
            upload.error = str(exc)
            log.warning("Parse failed for %s: %s", filename, exc)
            return upload, None, False

        upload.upload_type = result.upload_type
        upload.detected_format = workbook.fmt.value
        rows = self._persist(result, upload.id)
        upload.rows_ingested = rows
        upload.status = UploadStatus.PARSED

        report = ValidationReport(
            detected_type=result.upload_type,
            confidence=round(confidence, 3),
            detected_format=workbook.fmt.value,
            detected_headers=result.detected_headers,
            warnings=result.warnings,
            sheet_headers=result.sheet_headers,
            rows_ingested=rows,
            metrics=len(result.metrics),
            posts=len(result.posts),
            demographics=len(result.demographics),
        )
        upload.report = report.model_dump_json()
        return upload, report, False

    def _persist(self, result: ParseResult, upload_id: str) -> int:
        written = 0
        written += self.metrics.upsert_many(
            [
                {"metric_date": m.metric_date, "source": m.source, "metric": m.metric, "value": m.value}
                for m in result.metrics
            ],
            upload_id,
        )
        written += self.posts.upsert_many(
            [
                {
                    "post_url": p.post_url, "posted_at": p.posted_at, "post_type": p.post_type,
                    "title": p.title, "impressions": p.impressions, "clicks": p.clicks,
                    "reactions": p.reactions, "comments": p.comments, "reposts": p.reposts,
                    "engagement_rate": p.engagement_rate, "ctr": p.ctr,
                }
                for p in result.posts
            ],
            upload_id,
        )
        written += self.demographics.upsert_many(
            [
                {
                    "snapshot_date": d.snapshot_date, "dimension": d.dimension,
                    "category": d.category, "value": d.value,
                }
                for d in result.demographics
            ],
            upload_id,
        )
        return written
