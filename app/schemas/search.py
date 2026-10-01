from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class SearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    query: str = Field(min_length=1, max_length=1000, description="Search text")
    k: int = Field(default=5, ge=1, le=20, description="Number of results")


class SearchResult(BaseModel):
    chunk_id: UUID = Field(description="Unique identifier for the chunk")
    document_id: UUID = Field(description="Unique identifier for the document")
    content: str = Field(description="The content of the chunk")
    score: float = Field(description="RRF fusion score; higher is more relevant")
    vector_rank: int | None = Field(
        description="Position in vector search results; null if not in the vector top candidates"
    )
    keyword_rank: int | None = Field(
        description="Position in keyword search results; null if no keyword match"
    )


class SearchResponse(BaseModel):
    query: str = Field(description="The original search query")
    results: list[SearchResult] = Field(description="List of search results")
