import numpy as np

from pathlib import Path
from psycopg_pool import AsyncConnectionPool
from psycopg.rows import dict_row

HYBRID_SEARCH_SQL = (Path(__file__).parent / "sql" / "hybrid_search.sql").read_text(
    encoding="utf-8"
)


async def hybrid_search(
    pool: AsyncConnectionPool,
    query_text: str,
    query_vec: np.ndarray | list[float],
    k: int = 5,  # how many final results to return
    candidates: int = 20,  # how many results to take from each search before combining
    rrf_k: int = 60,  # points = 1 / (60 + position) the 60 in the formula
) -> list[dict]:
    if not query_text.strip():
        raise ValueError("query_text must not be empty or whitespace")
    if k < 1:
        raise ValueError("k must be at least 1")

    params = {
        "qvec": np.asarray(query_vec, dtype=np.float32),
        "qtext": query_text,
        "candidates": candidates,
        "rrf_k": rrf_k,
        "k": k,
    }

    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(HYBRID_SEARCH_SQL, params)
            return await cur.fetchall()
