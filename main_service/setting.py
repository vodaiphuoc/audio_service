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
    


    # ngrok + model_service
    NGROK_AUTH_TOKEN: str
    APPLICATION_PORT: int
    HTTPS_SERVER: str
    DEPLOY_DOMAIN: str
    ENDPOINT_ROUTER: str = ""

    # database
    DB_URL:str
    StorageBucketURL: str
    ACCOUNT_KEY_FILE: str
    PATH2ACCOUNT_KEY: str
    PROJECT_ID: str

    model_config = SettingsConfigDict(env_file="./secrets/.env")

SETTINGS = Settings()
