from langchain_openai import OpenAIEmbeddings
from app.core.config import Settings


def create_embeddings(settings: Settings) -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model=settings.openai.embedding_model,
        dimensions=settings.openai.embedding_dim,
        api_key=settings.openai.api_key,
        max_retries=2,
        timeout=10,
        check_embedding_ctx_length=False,
    )


async def embed_texts(
    embeddings: OpenAIEmbeddings, texts: list[str], dim: int
) -> list[list[float]]:
    if not texts:
        raise ValueError("texts must not be empty")

    vectors = await embeddings.aembed_documents(texts)
    for i, vector in enumerate(vectors):
        if len(vector) != dim:
            raise ValueError(f"expected {dim} dims, got {len(vector)} at index {i}")
    return vectors


async def embed_query(embeddings: OpenAIEmbeddings, text: str, dim: int) -> list[float]:
    if not text.strip():
        raise ValueError("text must not be empty")
    vector = await embeddings.aembed_query(text)
    if len(vector) != dim:
        raise ValueError(f"expected {dim} dims, got {len(vector)}")
    return vector
