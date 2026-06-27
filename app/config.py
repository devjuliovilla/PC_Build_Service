import os
from dataclasses import dataclass


def _as_bool(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    database_path: str = os.getenv("DATABASE_PATH", os.path.join("data", "ddtech.db"))
    headless: bool = _as_bool(os.getenv("HEADLESS"), default=True)
    playwright_timeout: int = int(os.getenv("PLAYWRIGHT_TIMEOUT", "45000"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()
    export_json_path: str = os.getenv("EXPORT_JSON_PATH", os.path.join("data", "ddtech_components.json"))
    export_chairs_json_path: str = os.getenv("EXPORT_CHAIRS_JSON_PATH", os.path.join("data", "ddtech_gaming_chairs.json"))
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    version: str = os.getenv("APP_VERSION", "1.0.0")


settings = Settings()
