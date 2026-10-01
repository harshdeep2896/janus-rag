import time

import psycopg
from psycopg import AsyncConnection
from pgvector.psycopg import register_vector_async
from psycopg_pool import AsyncConnectionPool

from app.core.config import Settings


async def create_pool(settings: Settings) -> AsyncConnectionPool:
    pool = AsyncConnectionPool(
        conninfo=settings.postgres.dsn.get_secret_value(),
        min_size=1,
        max_size=10,
        open=False,
        configure=_configure_connection,
    )
    await pool.open(wait=True, timeout=10)

    return pool


async def close_pool(pool: AsyncConnectionPool) -> None:
    await pool.close()


async def check_postgres(pool: AsyncConnectionPool) -> dict:
    start = time.perf_counter()
    async with pool.connection() as conn:
        cur = await conn.execute(
            query="SELECT extversion FROM pg_extension WHERE extname = 'vector'"
        )
        row = await cur.fetchone()

        if not row:
            raise RuntimeError("Missing Vector Extension")

        return {
            "status": "ok",
            "latency_ms": round((time.perf_counter() - start) * 1000, 1),
            "pgvector": row[0],
        }


async def check_schema(pool: AsyncConnectionPool, expected_head: str) -> dict:
    start = time.perf_counter()
    async with pool.connection() as conn:
        try:
            cur = await conn.execute(query="SELECT version_num FROM alembic_version")
        except psycopg.errors.UndefinedTable:
            raise RuntimeError(
                "alembic_version table missing, run alembic upgrade head"
            ) from None

        row = await cur.fetchone()
        current = row[0] if row else None

        if current != expected_head:
            raise RuntimeError(f"db at {current}, code expects {expected_head}")

        return {
            "status": "ok",
            "latency_ms": round((time.perf_counter() - start) * 1000, 1),
            "revision": current,
        }


async def _configure_connection(conn: AsyncConnection) -> None:
    await register_vector_async(conn)
    await conn.commit()
