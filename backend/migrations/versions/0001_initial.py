"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-11
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

upload_type = sa.Enum("followers", "visitors", "content", "unknown", name="upload_type")
upload_status = sa.Enum("pending", "parsed", "duplicate", "failed", name="upload_status")
demographic_dimension = sa.Enum(
    "job_function", "seniority", "industry", "location", "company_size",
    name="demographic_dimension",
)


def upgrade() -> None:
    op.create_table(
        "uploads",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("filename", sa.String(512), nullable=False),
        sa.Column("upload_type", upload_type, nullable=False),
        sa.Column("status", upload_status, nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("size_bytes", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("detected_format", sa.String(16)),
        sa.Column("rows_ingested", sa.Integer, nullable=False, server_default="0"),
        sa.Column("report", sa.Text),
        sa.Column("error", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("content_hash", name="uq_uploads_content_hash"),
    )
    op.create_index("ix_uploads_content_hash", "uploads", ["content_hash"])

    op.create_table(
        "daily_metrics",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("metric_date", sa.Date, nullable=False),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("metric", sa.String(64), nullable=False),
        sa.Column("value", sa.Float, nullable=False),
        sa.Column("upload_id", sa.String(36), sa.ForeignKey("uploads.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("metric_date", "metric", "source", name="uq_daily_metric"),
    )
    op.create_index("ix_daily_metrics_lookup", "daily_metrics", ["source", "metric", "metric_date"])

    op.create_table(
        "posts",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("post_url", sa.String(1024), nullable=False),
        sa.Column("posted_at", sa.DateTime(timezone=True)),
        sa.Column("post_type", sa.String(64)),
        sa.Column("title", sa.Text),
        sa.Column("impressions", sa.Integer, server_default="0"),
        sa.Column("clicks", sa.Integer, server_default="0"),
        sa.Column("reactions", sa.Integer, server_default="0"),
        sa.Column("comments", sa.Integer, server_default="0"),
        sa.Column("reposts", sa.Integer, server_default="0"),
        sa.Column("engagement_rate", sa.Float),
        sa.Column("ctr", sa.Float),
        sa.Column("upload_id", sa.String(36), sa.ForeignKey("uploads.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("post_url", name="uq_posts_post_url"),
    )
    op.create_index("ix_posts_post_url", "posts", ["post_url"])
    op.create_index("ix_posts_posted_at", "posts", ["posted_at"])

    op.create_table(
        "demographic_snapshots",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("snapshot_date", sa.Date, nullable=False),
        sa.Column("dimension", demographic_dimension, nullable=False),
        sa.Column("category", sa.String(256), nullable=False),
        sa.Column("value", sa.Float, nullable=False),
        sa.Column("upload_id", sa.String(36), sa.ForeignKey("uploads.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("snapshot_date", "dimension", "category", name="uq_demographic_snapshot"),
    )
    op.create_index("ix_demographic_lookup", "demographic_snapshots", ["dimension", "snapshot_date"])


def downgrade() -> None:
    op.drop_table("demographic_snapshots")
    op.drop_table("posts")
    op.drop_table("daily_metrics")
    op.drop_table("uploads")
    demographic_dimension.drop(op.get_bind(), checkfirst=True)
    upload_status.drop(op.get_bind(), checkfirst=True)
    upload_type.drop(op.get_bind(), checkfirst=True)
