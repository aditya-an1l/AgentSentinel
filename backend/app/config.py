import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    nebius_api_key: str = os.getenv("NEBIUS_API_KEY", "").strip()
    nebius_base_url: str = os.getenv("NEBIUS_BASE_URL", "https://api.tokenfactory.nebius.com/v1/").strip()
    nano_model: str = os.getenv("NEMOTRON_NANO_MODEL", "nvidia/Nemotron-3-Nano-30B-A3B").strip()
    ultra_model: str = os.getenv("NEMOTRON_ULTRA_MODEL", "nvidia/Nemotron-3-Ultra-253B").strip()
    model_timeout_seconds: float = float(os.getenv("MODEL_TIMEOUT_SECONDS", "12"))
    tavily_api_key: str = os.getenv("TAVILY_API_KEY", "").strip()
    database_path: str = os.getenv("DATABASE_PATH", "/data/agentsentinel.db")
    sandbox_url: str = os.getenv("SANDBOX_URL", "http://localhost:8100").rstrip("/")
    frontend_origin: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")

    @property
    def model_mode(self) -> str:
        return "nebius" if self.nebius_api_key else "mock"


settings = Settings()
