from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).parent.parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    domain: str = "localhost"
    api_secret_key: str = ""
    admin_username: str = "admin"
    admin_password: str = ""

    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    jwt_algorithm: str = "HS256"

    squid_log: str = "/var/log/squid/access.log"
    domains_file: str = str(ROOT_DIR / "squid" / "domains.txt")
    htpasswd_file: str = str(ROOT_DIR / "data" / "passwd")
    db_url: str = f"sqlite+aiosqlite:///{ROOT_DIR / 'data' / 'db.sqlite3'}"
    squid_container: str = "pi-gateway-squid-1"

    @field_validator("api_secret_key")
    @classmethod
    def secret_key_must_be_set(cls, v: str) -> str:
        if not v or len(v) < 32:
            raise ValueError("API_SECRET_KEY must be at least 32 characters")
        return v

    @field_validator("admin_password")
    @classmethod
    def admin_password_must_be_set(cls, v: str) -> str:
        if not v:
            raise ValueError("ADMIN_PASSWORD must be set")
        return v


settings = Settings()