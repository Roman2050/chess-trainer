from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    stockfish_path: str = "/usr/games/stockfish"
    llm_provider: str = "ollama"
    engine_depth: int = 18

    model_config = {"env_file": ".env"}

settings = Settings()