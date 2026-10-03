/*
 * Upsert chunks for a given document.
 * If a chunk with the same document_id and chunk_index exists, it will be updated.
 * Otherwise, a new chunk will be inserted.
 */

INSERT INTO chunks (document_id, chunk_index, content, token_count, embedding)
SELECT %(document_id)s, idx, content, token_count, embedding::vector
FROM unnest(
    %(chunk_indexes)s::int[],
    %(contents)s::text[],
    %(token_counts)s::int[],
    %(embeddings)s::text[]
) AS t(idx, content, token_count, embedding)
ON CONFLICT (document_id, chunk_index)
DO UPDATE SET content = excluded.content,
              token_count = excluded.token_count,
              embedding = excluded.embedding