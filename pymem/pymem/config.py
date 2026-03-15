"""PyMem configuration settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    port: int = 8090
    api_key: str = "pymem-dev-key"
    max_documents: int = 10000
    default_chunk_size: int = 500
    default_overlap: int = 50
    model_config = {"env_prefix": "PYMEM_"}


settings = Settings()
