from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Cryptography(BaseSettings):
    CRYPTOGRAPHY_SECRET_KEY: str


class Jwt(BaseSettings):
    JWT_ALGORITHM: str = "HS256"
    JWT_SECRET_KEY: str
    JWT_EXPIRED_SECONDS: int = 43200


class Sentry(BaseSettings):
    SENTRY_DSN: str | None = None


class Postgres(BaseSettings):
    POSTGRES_HOST: str

    @property
    def psycopg(self) -> str:
        return self.POSTGRES_HOST.replace("asyncpg", "psycopg2")

    @property
    def asyncpg(self) -> str:
        return self.POSTGRES_HOST


class Redis(BaseSettings):
    REDIS_HOST: str


class Kafka(BaseSettings):
    KAFKA_HOST: str
    KAFKA_TOPIC_INGRESS: str
    KAFKA_GROUP_ID: str


class Minio(BaseSettings):
    MINIO_HOST: str
    MINIO_ACCESS_KEY_ID: str
    MINIO_SECRET_ACCESS_KEY: str
    MINIO_BUCKET: str = "media"


class Scheduler(BaseSettings): ...


configs = [
    Cryptography,
    Jwt,
    Sentry,
    Postgres,
    Redis,
    Kafka,
    Minio,
    Scheduler,
]


class Settings(*configs):  # type: ignore[misc]
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")


settings = Settings()
