from pydantic import (
    BaseModel, 
    SecretStr,
    field_validator
)
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict
)
from pathlib import Path
from typing import Literal
from functools import lru_cache

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
    def validate_path(cls, v: Path) ->Path:
        if v.is_absolute():
            return v
        return BASE_DIR / v

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

class Settings(BaseSettings):
    app: AppSettings
    postgres: PostgresSettings
    kafka: KafkaSettings
    redis: RedisSettings
    mongo: MongoSettings
    temporal: TemporalSettings
    openai: OpenAISettings

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_nested_delimiter="__",
        env_file_encoding="utf-8"
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()
