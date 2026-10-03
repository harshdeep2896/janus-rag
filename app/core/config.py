from functools import lru_cache
from pathlib import Path
from typing import Literal, Self

from pydantic import BaseModel, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class AppSettings(BaseModel):
    env: Literal["dev", "staging", "prod"]
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class PostgresSettings(BaseModel):
    dsn: SecretStr


class KafkaSettings(BaseModel):
    bootstrap_servers: str
    ssl_ca: Path
    ssl_cert: Path
    ssl_key: Path

    @field_validator("ssl_ca", "ssl_cert", "ssl_key")
    @classmethod
    def validate_path(cls, v: Path) -> Path:
        if v.is_absolute():
            return v
        return BASE_DIR / v


class StorageSettings(BaseModel):
    raw_dir: Path = Field(default=Path("data/raw"), validate_default=True)

    @field_validator("raw_dir")
    @classmethod
    def validate_path(cls, v: Path) -> Path:
        return v if v.is_absolute() else BASE_DIR / v


class RedisSettings(BaseModel):
    url: SecretStr


class MongoSettings(BaseModel):
    uri: SecretStr
    db: str


class TemporalSettings(BaseModel):
    host: str
    namespace: str


class OpenAISettings(BaseModel):
    api_key: SecretStr
    embedding_model: str = "text-embedding-3-small"
    embedding_dim: int = 1536


class IngestionSettings(BaseModel):
    chunk_max_tokens: int = Field(default=400, ge=50, le=8000)
    chunk_overlap_tokens: int = Field(default=50, ge=0)
    embed_batch_size: int = Field(default=64, ge=1, le=2048)

    @model_validator(mode="after")
    def check_overlap(self) -> Self:
        if self.chunk_overlap_tokens >= self.chunk_max_tokens:
            raise ValueError("chunk_overlap_tokens must be less than chunk_max_tokens")
        return self


class Settings(BaseSettings):
    app: AppSettings
    postgres: PostgresSettings
    kafka: KafkaSettings
    storage: StorageSettings = Field(default_factory=StorageSettings)
    redis: RedisSettings
    mongo: MongoSettings
    temporal: TemporalSettings
    openai: OpenAISettings
    ingestion: IngestionSettings = Field(default_factory=IngestionSettings)

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env", env_nested_delimiter="__", env_file_encoding="utf-8"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
