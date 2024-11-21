from pydantic import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_host: str = 'localhost'
    app_port: int = 8000
    db_url: str = 'postgresql://vet_user:12345@db:5432/vet_db'
    async_db_url: str = 'postgresql+asyncpg://vet_user:12345@db:5432/vet_db'

    secret_key: str
    access_token_expire_hours: int = 99999
    access_token_alg: str = 'HS256'
    mail_username: str
    mail_password: str
    mail_from: str
    mail_port: str
    mail_server: str
    mail_from_name: str

    class Config:
        env_file = '.env'
        extra = "allow"


@lru_cache()
def get_settings():
    return Settings()
