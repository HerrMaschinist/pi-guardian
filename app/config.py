from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    ROUTER_HOST: str = "0.0.0.0"
    ROUTER_PORT: int = 8071
    LOG_LEVEL: str = "INFO"

    model_config = {"env_file": ".env"}


settings = Settings()
