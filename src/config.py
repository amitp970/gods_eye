from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    HTTP_SERVER_IP: str
    HTTP_SERVER_PORT: int

    ADMIN_USER: str
    ADMIN_PASS: str
    DATABASE_URL: str

settings = Settings()

print(settings.model_dump_json())