import os
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()


class Settings:
    def __init__(self) -> None:
        self.POSTGRES_URL = os.getenv("POSTGRES_URL", "")
        self.REDIS_URL = os.getenv("REDIS_URL", "")
        self.MONITORING_HOST = os.getenv("MONITORING_HOST", "0.0.0.0")
        self.MONITORING_PORT = int(os.getenv("MONITORING_PORT", "9000"))
        self.ENABLE_WEBSOCKETS = os.getenv("ENABLE_WEBSOCKETS", "false").lower() == "true"
        self.ENABLE_SCHEDULER = os.getenv("ENABLE_SCHEDULER", "false").lower() == "true"
        self.SCHEDULER_INTERVAL_SECONDS = int(os.getenv("SCHEDULER_INTERVAL_SECONDS", "5"))
        self.MONITORING_API_KEY = os.getenv("MONITORING_API_KEY")

@lru_cache
def get_settings() -> Settings:
    return Settings()
