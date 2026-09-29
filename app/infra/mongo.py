import time
from pymongo import AsyncMongoClient

from app.core.config import Settings

def create_mongo(settings: Settings) -> AsyncMongoClient:
    return AsyncMongoClient(
        settings.mongo.uri.get_secret_value(),
        serverSelectionTimeoutMS=5000
    )

async def close_mongo(client: AsyncMongoClient) -> None:
    await client.close()

async def check_mongo(client: AsyncMongoClient) -> dict:
    start = time.perf_counter()
    await client.admin.command("ping")
    return {
        "status": "ok",
        "latency_ms": round((time.perf_counter() - start) * 1000, 1)
    }