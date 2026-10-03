from dataclasses import dataclass

import tiktoken
from langchain_text_splitters import RecursiveCharacterTextSplitter

_ENCODER = tiktoken.get_encoding("cl100k_base")


@dataclass(frozen=True, slots=True)
class TextChunk:
    index: int
    content: str
    token_count: int


def chunk_text(
    text: str, *, max_tokens: int = 400, overlap_tokens: int = 50
) -> list[TextChunk]:
    if max_tokens < 1:
        raise ValueError("max_tokens must be greater than 0")
    if overlap_tokens < 0 or overlap_tokens >= max_tokens:
        raise ValueError(
            "overlap_tokens must be greater than or equal to 0 and less than max_tokens"
        )

    if not text.strip():
        return []

    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name="cl100k_base",
        chunk_size=max_tokens,
        chunk_overlap=overlap_tokens,
        disallowed_special=(),
    )

    chunks = splitter.split_text(text)
    return [
        TextChunk(
            index=i,
            content=chunk,
            token_count=len(_ENCODER.encode(chunk, disallowed_special=())),
        )
        for i, chunk in enumerate(chunks)
    ]
