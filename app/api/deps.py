from typing import Annotated

from fastapi import Request, Depends
from langchain_openai import OpenAIEmbeddings
from psycopg_pool import AsyncConnectionPool

from app.core.config import Settings, get_settings


def get_pg_pool(request: Request) -> AsyncConnectionPool:
    return request.app.state.pg_pool


def get_embeddings(request: Request) -> OpenAIEmbeddings:
    return request.app.state.embeddings


PgPoolDep = Annotated[AsyncConnectionPool, Depends(get_pg_pool)]
EmbeddingsDep = Annotated[OpenAIEmbeddings, Depends(get_embeddings)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
