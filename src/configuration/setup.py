from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Postgres(BaseSettings):
    POSTGRES: bool = False
    POSTGRES_HOST: str | None = None

    @property
    def psycopg(self) -> str | None:
        return self.POSTGRES_HOST.replace("asyncpg", "psycopg2") if self.POSTGRES_HOST else None

    @property
    def asyncpg(self) -> str | None:
        return self.POSTGRES_HOST


class Redis(BaseSettings):
    REDIS: bool = False
    REDIS_HOST: str | None = None

    @property
    def url(self) -> str:
        if not self.REDIS_HOST:
            raise ValueError("REDIS_HOST must be set")
        return self.REDIS_HOST


class Kafka(BaseSettings):
    KAFKA: bool = False
    KAFKA_HOST: str | None = None
    KAFKA_TOPIC_INGRESS: str | None = None
    KAFKA_GROUP_ID: str | None = None


class Minio(BaseSettings):
    MINIO: bool = False
    MINIO_HOST: str | None = None
    MINIO_ACCESS_KEY_ID: str | None = None
    MINIO_SECRET_ACCESS_KEY: str | None = None
    MINIO_BUCKET: str | None = "media"


configs = [
    Postgres,
    Redis,
    Kafka,
    Minio,
]


class Settings(*configs):  # type: ignore[misc]
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")


settings = Settings()
