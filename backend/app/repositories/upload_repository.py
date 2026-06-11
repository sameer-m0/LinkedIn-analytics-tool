from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.upload import Upload


class UploadRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_hash(self, content_hash: str) -> Upload | None:
        return self.db.scalar(select(Upload).where(Upload.content_hash == content_hash))

    def add(self, upload: Upload) -> Upload:
        self.db.add(upload)
        self.db.flush()
        return upload

    def list(self, limit: int = 100) -> list[Upload]:
        return list(
            self.db.scalars(select(Upload).order_by(Upload.created_at.desc()).limit(limit))
        )

    def get(self, upload_id: str) -> Upload | None:
        return self.db.get(Upload, upload_id)
