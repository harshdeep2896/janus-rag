import asyncio
import time
from app.core.config import Settings
from confluent_kafka.admin import AdminClient

REQUIRED_TOPICS = {"documents.uploaded", "documents.indexed", "documents.dlq"}

def build_kafka_config(settings: Settings) -> dict:
    return {
        "bootstrap.servers": settings.kafka.bootstrap_servers,
        "security.protocol": "SSL",
        "ssl.ca.location": str(settings.kafka.ssl_ca),
        "ssl.certificate.location": str(settings.kafka.ssl_cert),
        "ssl.key.location": str(settings.kafka.ssl_key)
    }

def create_kafka_admin(settings: Settings) -> AdminClient:
    return AdminClient(conf=build_kafka_config(settings))

async def check_kafka(admin: AdminClient, timeout: float = 2) -> dict:
    start = time.perf_counter()
    metadata = await asyncio.to_thread(
        admin.list_topics,
        timeout=timeout # seconds
    )

    missing = REQUIRED_TOPICS - set(metadata.topics.keys())
    if missing:
        raise RuntimeError(f"Missing required topics: {sorted(missing)}")
    
    return {
        "status": "ok",
        "latency_ms": round((time.perf_counter() - start)* 1000, 1),
        "brokers": len(metadata.brokers),
        "topics": len(metadata.topics)
    }