"""PyGate configuration settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    port: int = 8443
    api_key: str = "pygate-dev-key"
    default_model: str = "claude-sonnet-4-20250514"
    rate_limit_per_minute: int = 60
    model_config = {"env_prefix": "PYGATE_"}


settings = Settings()
