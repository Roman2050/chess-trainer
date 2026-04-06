from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    stockfish_path: str = "/usr/games/stockfish"
    llm_provider: str = "ollama"
    engine_depth: int = 18
    llm_provider: str = "ollama"
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    anthropic_api_key: str = ""

    model_config = {"env_file": ".env"}

settings = Settings()