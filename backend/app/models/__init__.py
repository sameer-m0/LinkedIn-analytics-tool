"""Model package — importing registers all tables on ``Base.metadata``."""
from app.models.upload import Upload, UploadType, UploadStatus  # noqa: F401
from app.models.daily_metric import DailyMetric  # noqa: F401
from app.models.post import Post  # noqa: F401
from app.models.demographic import DemographicSnapshot, DemographicDimension  # noqa: F401

__all__ = [
    "Upload",
    "UploadType",
    "UploadStatus",
    "DailyMetric",
    "Post",
    "DemographicSnapshot",
    "DemographicDimension",
]
