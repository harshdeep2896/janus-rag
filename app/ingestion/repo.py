from pathlib import Path
from uuid import UUID

from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

_SQL_DIR = Path(__file__).parent / "SQL"
_GET_DOCUMENT_SQL = (_SQL_DIR / "get_document.sql").read_text(encoding="utf-8")
_UPDATE_DOCUMENT_STATUS_SQL = (_SQL_DIR / "update_document_status.sql").read_text(
    encoding="utf-8"
)
_UPSERT_CHUNKS_SQL = (_SQL_DIR / "upsert_chunks.sql").read_text(encoding="utf-8")


async def get_document(pool: AsyncConnectionPool, document_id: UUID) -> dict | None:
    """Return {content_hash, filename, mime_type} for document_id, or None if missing."""
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                query=_GET_DOCUMENT_SQL, params={"document_id": document_id}
            )
            return await cur.fetchone()


async def update_document_status(
    pool: AsyncConnectionPool,
    document_id: UUID,
    status: str,
    error: str | None = None,
) -> None:
    """Set documents.status (and error, usually None) for document_id."""
    async with pool.connection() as conn:
        await conn.execute(
            query=_UPDATE_DOCUMENT_STATUS_SQL,
            params={"document_id": document_id, "status": status, "error": error},
        )

async def upsert_chunks(
        pool: AsyncConnectionPool,
        document_id: UUID,
        chunk_indexes: list[int],
        contents: list[str],
        token_counts: list[int],
        embeddings: list[list[float]],
) -> None:
    """Upsert one batch of chunks for document_id. All 4 lists must be the same length."""
    async with pool.connection() as conn:
        embedding_literals = [
            "[" + ",".join(map(str, vec)) + "]" for vec in embeddings
        ]
        await conn.execute(
            query=_UPSERT_CHUNKS_SQL,
            params={
                "document_id": document_id,
                "chunk_indexes": chunk_indexes,
                "contents": contents,
                "token_counts": token_counts,
                "embeddings": embedding_literals
            },
        )