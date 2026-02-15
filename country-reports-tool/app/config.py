from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    box_client_id: str
    box_client_secret: str
    box_enterprise_id: str
    box_folder_id: str

    pdf_dir: Path = BASE_DIR / "data" / "pdfs"
    chroma_dir: Path = BASE_DIR / "data" / "chroma"

    model_config = {"env_file": BASE_DIR / ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
