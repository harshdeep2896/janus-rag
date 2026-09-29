"""create chunks

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-29 16:41:48.764041

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0002'
down_revision: Union[str, Sequence[str], None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE chunks (
            id           uuid        PRIMARY KEY DEFAULT uuidv7(),
            document_id  uuid        NOT NULL,
            chunk_index  integer     NOT NULL,
            content      text        NOT NULL,
            token_count  integer     NOT NULL,
            metadata     jsonb       NOT NULL DEFAULT '{}'::jsonb,
            embedding    vector(1536) NOT NULL,
            tsv          tsvector    GENERATED ALWAYS AS (to_tsvector('english', content)) STORED,
            created_at   timestamptz NOT NULL DEFAULT now(),

            CONSTRAINT fk_chunks_document_id FOREIGN KEY (document_id)
                REFERENCES documents (id) ON DELETE CASCADE,
            CONSTRAINT uq_chunks_document_id_chunk_index UNIQUE (document_id, chunk_index),
            CONSTRAINT ck_chunks_chunk_index CHECK (chunk_index >= 0),
            CONSTRAINT ck_chunks_token_count CHECK (token_count >= 0)
        )
        """
    )

    op.execute(
        """
        CREATE INDEX ix_chunks_embedding_hnsw
            ON chunks USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64)
        """
    )

    op.execute("CREATE INDEX ix_chunks_tsv_gin ON chunks USING gin (tsv)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS chunks")
