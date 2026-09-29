import time
from redis.asyncio import Redis

from app.core.config import Settings

def create_redis(settings: Settings) -> Redis:
    return Redis.from_url(
        url=settings.redis.url.get_secret_value(),
        decode_responses=True
    )

async def close_redis(client: Redis) -> None:
    await client.aclose()

async def check_redis(client: Redis) -> dict:
    start = time.perf_counter()
    await client.ping()
    return {
        "status": "ok",
        "latency_ms": round((time.perf_counter() - start) * 1000, 1)   
    }