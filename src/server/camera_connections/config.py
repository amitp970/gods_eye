from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    HTTP_SERVER_IP: str
    HTTP_SERVER_PORT: int
    HTTP_SERVER_CAMERA_LISTEN_PORT: int

settings = Settings()

print(settings.model_dump_json())