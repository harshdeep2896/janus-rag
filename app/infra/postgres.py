import time

from psycopg_pool import AsyncConnectionPool
from sqlalchemy import Text

from app.core.config import Settings

async def create_pool(settings: Settings) -> AsyncConnectionPool:
    pool = AsyncConnectionPool(
        conninfo=settings.postgres.dsn.get_secret_value(),
        min_size=1,
        max_size=10,
        open=False
    )
    await pool.open(
        wait=True,
        timeout=10
    )

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
            raise RuntimeError(
                "Missing Vector Extension"
            )

        return {"status": "ok", 
                "latency_ms": round((time.perf_counter() - start) * 1000, 1), 
                "pgvector": row[0]}