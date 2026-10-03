import asyncio
import logging

from temporalio.client import Client
from temporalio.worker import Worker

from app.core.config import get_settings
from app.infra.embeddings import create_embeddings
from app.infra.postgres import close_pool, create_pool
from app.ingestion.activities import IngestionActivities
from app.ingestion.workflows import IngestDocumentWorkflow


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TASK_QUEUE = "janus-ingestion"

async def main() -> None:
    settings = get_settings()

    pool = await create_pool(settings)
    embeddings = create_embeddings(settings)
    activities = IngestionActivities(pool=pool, embeddings=embeddings, settings=settings)

    client = await Client.connect(
        settings.temporal.host, namespace=settings.temporal.namespace
    )

    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[IngestDocumentWorkflow],
        activities=[
            activities.mark_processing,
            activities.count_chunks,
            activities.embed_and_store_batch,
            activities.mark_status,
        ],
    )

    logger.info("worker started, task_queue=%s", TASK_QUEUE)
    try:
        await worker.run()
    finally:
        await close_pool()

if __name__ == "__main__":
    with asyncio.Runner(loop_factory=asyncio.SelectorEventLoop) as runner:
        runner.run(main())
