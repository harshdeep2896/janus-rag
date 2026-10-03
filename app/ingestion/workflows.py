from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from app.ingestion.activities import IngestionActivities
    from app.ingestion.errors import IngestionError

_RETRY_POLICY = RetryPolicy(
    maximum_attempts=3,
    non_retryable_error_types=[
        "IngestionError",
        "UnsupportedMimeTypeError",
        "DocumentParseError",
        "EmptyDocumentError",
    ],
)

_START_TO_CLOSE = timedelta(minutes=5)


@workflow.defn
class IngestDocumentWorkflow:
    @workflow.run
    async def run(self, document_id: str) -> str:
        try:
            # Mark the document as processing before doing any work, so that if the
            # workflow fails, we can retry it without re-downloading the document.
            await workflow.execute_activity_method(
                IngestionActivities.mark_processing,
                document_id,
                start_to_close_timeout=_START_TO_CLOSE,
                retry_policy=_RETRY_POLICY,
            )

            # Load the file, parse it, chunk it, and return how many chunks there are.
            # The chunks themselves never leave the activity (Temporal history has a
            # payload size limit); only this small integer comes back to the workflow.
            total = await workflow.execute_activity_method(
                IngestionActivities.count_chunks,
                document_id,
                start_to_close_timeout=_START_TO_CLOSE,
                retry_policy=_RETRY_POLICY,
            )

            # Embed and upsert the chunks in fixed-size batches, one activity call per
            # batch. Each call re-reads and re-chunks the file (cheap, deterministic),
            # then embeds and upserts only its own [start:end] slice. If one batch
            # fails, only that batch retries — earlier batches are already committed
            # to chunks, and upsert_chunks's ON CONFLICT makes a retried batch safe.
            batch_size = 64
            for start in range(0, total, batch_size):
                end = min(start + batch_size, total)
                await workflow.execute_activity_method(
                    IngestionActivities.embed_and_store_batch,
                    args=[document_id, start, end],
                    start_to_close_timeout=_START_TO_CLOSE,
                    retry_policy=_RETRY_POLICY,
                )

            # All batches upserted successfully: mark the document indexed.
            await workflow.execute_activity_method(
                IngestionActivities.mark_status,
                args=[document_id, "indexed", None],
                start_to_close_timeout=_START_TO_CLOSE,
                retry_policy=_RETRY_POLICY,
            )
            return "indexed"
        except Exception as e:
            # Something failed even after retries (or hit a non-retryable error like
            # EmptyDocumentError). Record the failure on the document so it doesn't
            # stay stuck in "processing" forever, then re-raise so the workflow
            # itself also shows as failed in the Temporal UI.
            # maximum_attempts=1: don't retry this cleanup step itself, to avoid
            # looping if the database write that reports the failure also fails.
            await workflow.execute_activity_method(
                IngestionActivities.mark_status,
                args=[document_id, "failed", str(e)],
                start_to_close_timeout=_START_TO_CLOSE,
                retry_policy=RetryPolicy(maximum_attempts=1),
            )
            raise
