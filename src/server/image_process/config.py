from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):

    DATABASE_URL: str
    FAISS_PATH: str
    ROOT_PATH_IMAGES: str

settings = Settings()