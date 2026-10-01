from fastapi import APIRouter, HTTPException, status
import openai
import logging

import psycopg

from app.api.deps import PgPoolDep, EmbeddingsDep, SettingsDep
from app.schemas.search import SearchRequest, SearchResponse
from app.services.search import search_chunks

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Search"])


@router.post(
    "/search",
    response_model=SearchResponse,
    responses={
        status.HTTP_502_BAD_GATEWAY: {"description": "Embedding service failed"},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Database unavailable"},
    },
)
async def search(
    payload: SearchRequest,
    pool: PgPoolDep,
    embeddings: EmbeddingsDep,
    settings: SettingsDep,
) -> SearchResponse:
    try:
        results = await search_chunks(
            pool=pool,
            embeddings=embeddings,
            query=payload.query,
            k=payload.k,
            embedding_dim=settings.openai.embedding_dim,
        )
    except openai.APIError as e:
        logger.exception("embedding failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail="Embedding service failed"
        ) from e
    except psycopg.OperationalError as e:
        logger.exception("database unavailable")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from e

    return SearchResponse(query=payload.query, results=results)
