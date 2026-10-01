from psycopg_pool import AsyncConnectionPool
from langchain_openai import OpenAIEmbeddings

from app.infra.embeddings import embed_query
from app.retrieval.hybrid import hybrid_search
from app.schemas.search import SearchResult


async def search_chunks(
    *,
    pool: AsyncConnectionPool,
    embeddings: OpenAIEmbeddings,
    query: str,
    k: int,
    embedding_dim: int,
) -> list[SearchResult]:
    vector = await embed_query(embeddings, query, embedding_dim)
    rows = await hybrid_search(pool, query, vector, k=k)

    # model_validate turns each dict row into a SearchResult,
    # and also checks the types. If a column is ever renamed in the SQL,
    # this fails loudly here instead of sending a broken response.
    return [SearchResult.model_validate(row) for row in rows]
