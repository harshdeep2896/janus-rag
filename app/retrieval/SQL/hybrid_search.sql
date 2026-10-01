/**
Notes:

COALESCE(s.id, l.id): after a FULL OUTER JOIN, a chunk found by only one search has NULL on the other side. 
This picks whichever id exists.
COALESCE(..., 0): if a search didn't find the chunk, its rank is NULL, so 1.0 / (60 + NULL) is NULL. 
This turns that into 0 points.
::float8: without it, 1.0 / ... returns numeric, which arrives in Python as Decimal. 
The cast gives you a normal float.
Getting dicts back: use conn.cursor(row_factory=dict_row) (from psycopg.rows import dict_row). 
The column aliases (chunk_id, score, ...) become the dict keys directly.
Limit to remember: HNSW looks at 40 candidates by default (hnsw.ef_search = 40). 
If you ever set candidates above 40, the vector part may return fewer rows than asked. 
The default of 20 is fine.
**/

WITH semantic AS (
    SELECT id,
           row_number() OVER (ORDER BY embedding <=> %(qvec)s) AS rank
    FROM chunks
    ORDER BY embedding <=> %(qvec)s
    LIMIT %(candidates)s
),
lexical AS (
    SELECT id,
           row_number() OVER (ORDER BY ts_rank_cd(tsv, q) DESC) AS rank
    FROM chunks,
         websearch_to_tsquery('english', %(qtext)s) AS q
    WHERE tsv @@ q
    ORDER BY ts_rank_cd(tsv, q) DESC
    LIMIT %(candidates)s
),
fused AS (
    SELECT COALESCE(s.id, l.id) AS id,
           s.rank AS vector_rank,
           l.rank AS keyword_rank,
           (COALESCE(1.0 / (%(rrf_k)s + s.rank), 0)
          + COALESCE(1.0 / (%(rrf_k)s + l.rank), 0))::float8 AS score
    FROM semantic s
    FULL OUTER JOIN lexical l ON s.id = l.id
)
SELECT c.id AS chunk_id,
       c.document_id,
       c.content,
       f.score,
       f.vector_rank,
       f.keyword_rank
FROM fused f
JOIN chunks c ON c.id = f.id
ORDER BY f.score DESC
LIMIT %(k)s