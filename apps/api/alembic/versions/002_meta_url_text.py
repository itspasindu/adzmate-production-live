"""Widen Meta asset URL columns — Facebook CDN URLs can exceed 500 chars.

Revision ID: 002_meta_url_text
Revises: 001_initial
Create Date: 2026-09-01
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "002_meta_url_text"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "meta_pages",
        "picture_url",
        existing_type=sa.String(500),
        type_=sa.Text(),
        existing_nullable=True,
    )
    op.alter_column(
        "meta_instagram_accounts",
        "profile_picture_url",
        existing_type=sa.String(500),
        type_=sa.Text(),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "meta_instagram_accounts",
        "profile_picture_url",
        existing_type=sa.Text(),
        type_=sa.String(500),
        existing_nullable=True,
    )
    op.alter_column(
        "meta_pages",
        "picture_url",
        existing_type=sa.Text(),
        type_=sa.String(500),
        existing_nullable=True,
    )
