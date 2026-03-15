from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    port: int = 8080
    api_key: str = "sandbox-dev-key"
    max_sandboxes: int = 100
    default_timeout: int = 300
    default_memory_mb: int = 512
    model_config = {"env_prefix": "PYSANDBOX_"}


settings = Settings()
