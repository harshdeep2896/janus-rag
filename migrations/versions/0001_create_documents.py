"""create documents

Revision ID: 0001
Revises: 
Create Date: 2026-09-29 16:28:27.378916

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.execute(
        """
        CREATE TABLE documents (
            id            uuid        PRIMARY KEY DEFAULT uuidv7(),
            content_hash  text        NOT NULL,
            filename      text        NOT NULL,
            mime_type     text        NOT NULL,
            size_bytes    bigint      NOT NULL,
            status        text        NOT NULL DEFAULT 'uploaded',
            error         text,
            created_at    timestamptz NOT NULL DEFAULT now(),
            updated_at    timestamptz NOT NULL DEFAULT now(),

            CONSTRAINT uq_documents_content_hash UNIQUE (content_hash),
            CONSTRAINT ck_documents_size_bytes CHECK (size_bytes >= 0),
            CONSTRAINT ck_documents_status
                CHECK (status IN ('uploaded', 'processing', 'indexed', 'failed'))
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS documents")
