from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import ClassVar

class Settings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASSWORD: str
    BASE_URL: ClassVar[str]
    GEMINI_API_KEY: str
    
    model_config = SettingsConfigDict(env_file="../.env")

SETTINGS = Settings()
