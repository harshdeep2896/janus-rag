import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.infra.embeddings import create_embeddings
from app.infra.migrations import get_alembic_head
from app.infra.postgres import create_pool, close_pool
from app.infra.kafka import create_kafka_admin, check_kafka
from app.infra.mongo import create_mongo, close_mongo, check_mongo
from app.infra.redis import create_redis, close_redis, check_redis
from app.infra.temporal import create_temporal
from app.api.health import router as health_router
from app.api.search import router as search_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.alembic_head = get_alembic_head()
    app.state.pg_pool = await create_pool(settings)
    app.state.redis = create_redis(settings)
    app.state.mongo = create_mongo(settings)
    app.state.temporal = await create_temporal(settings)
    app.state.kafka_admin = create_kafka_admin(settings)
    app.state.embeddings = create_embeddings(settings)

    # Warm-up: open lazy connections now, so /health/ready doesn't pay cold-start cost
    for name, check, client in [
        ("redis", check_redis, app.state.redis),
        ("mongo", check_mongo, app.state.mongo),
        ("kafka", lambda c: check_kafka(c, timeout=10), app.state.kafka_admin),
    ]:
        try:
            await check(client)
        except Exception as exc:
            logger.warning("Warm-up failed for %s: %s", name, exc)

    try:
        yield
    finally:
        await close_mongo(app.state.mongo)
        await close_redis(app.state.redis)
        await close_pool(app.state.pg_pool)


app = FastAPI(title="Janus", lifespan=lifespan)

app.include_router(router=health_router)
app.include_router(router=search_router)