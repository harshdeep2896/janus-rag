import time

from temporalio.client import Client

from app.core.config import Settings

async def create_temporal(settings: Settings) -> Client:
    return await Client.connect(target_host=settings.temporal.host,
                                namespace=settings.temporal.namespace)

async def check_temporal(client: Client) -> dict:
    start = time.perf_counter()
    flag = await client.service_client.check_health()
    if not flag:
        raise RuntimeError("Temporal service is not healthy")
    return {
        "status": "ok",
        "latency_ms": round((time.perf_counter() - start) * 1000, 1)
    }
