from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "radio-medical-ai"
    api_prefix: str = "/api/v1"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"
    ollama_temperature: float = 0.2

    rag_persist_dir: str = ".chroma"
    rag_collection: str = "medical_training_kb"

    mcp_server_script: str = "mcp/medical_mcp_server.py"


settings = Settings()

