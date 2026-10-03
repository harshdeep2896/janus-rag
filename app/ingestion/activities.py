from dataclasses import dataclass
from uuid import UUID

from langchain_openai import OpenAIEmbeddings
from psycopg_pool import AsyncConnectionPool
from temporalio import activity

from app.core.config import Settings
from app.infra.embeddings import embed_texts
from app.infra.storage import read_raw
from app.ingestion.chunking import TextChunk, chunk_text
from app.ingestion.errors import EmptyDocumentError, IngestionError
from app.ingestion.parsing import parse_document
from app.ingestion.repo import get_document, update_document_status, upsert_chunks


@dataclass
class IngestionActivities:
    pool: AsyncConnectionPool
    embeddings: OpenAIEmbeddings
    settings: Settings

    async def _load_and_chunk(self, document_id: UUID) -> list[TextChunk]:
        doc = await get_document(self.pool, document_id)
        if not doc:
            raise IngestionError(f"document not found: {document_id}")

        data = await read_raw(self.settings.storage.raw_dir, doc["content_hash"])
        text = parse_document(data, doc["mime_type"])
        chunks = chunk_text(
            text,
            max_tokens=self.settings.ingestion.chunk_max_tokens,
            overlap_tokens=self.settings.ingestion.chunk_overlap_tokens,
        )
        if not chunks:
            raise EmptyDocumentError(f"no text extracted: {document_id}")
        return chunks

    @activity.defn
    async def mark_processing(self, document_id: UUID) -> None:
        await update_document_status(self.pool, document_id, "processing")

    @activity.defn
    async def count_chunks(self, document_id: UUID) -> int:
        chunks = await self._load_and_chunk(document_id)
        return len(chunks)

    @activity.defn
    async def embed_and_store_batch(
        self, document_id: UUID, start: int, end: int
    ) -> int:
        chunks = await self._load_and_chunk(document_id)
        batch = chunks[start:end]

        vectors = await embed_texts(
            self.embeddings,
            [c.content for c in batch],
            self.settings.openai.embedding_dim,
        )

        await upsert_chunks(
            self.pool,
            document_id,
            chunk_indexes=[c.index for c in batch],
            contents=[c.content for c in batch],
            token_counts=[c.token_count for c in batch],
            embeddings=vectors,
        )

        return len(batch)

    @activity.defn
    async def mark_status(
        self, document_id: UUID, status: str, error: str | None = None
    ) -> None:
        await update_document_status(self.pool, document_id, status, error)
