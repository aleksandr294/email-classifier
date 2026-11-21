import functools
from pathlib import Path

import dotenv
import pydantic
import pydantic_settings

dotenv.load_dotenv()


class Config(pydantic_settings.BaseSettings):
    POSTGRES_URL: pydantic.PostgresDsn

    ANTHROPIC_API_KEY: str
    LLM_MODEL_NAME: str

    CLASSIFY_WORKER_PAUSE_SECONDS: int = 10
    RETRY_WORKER_PAUSE_SECONDS: int = 60 * 10
    STALE_PROCESSING_MINUTES: int = 15

    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    FILES_FOLDER: str = "email_files"

    MAX_FILE_SIZE: int = 10 * 1024 * 1024

    model_config = pydantic.ConfigDict(env_file=".env")


@functools.lru_cache
def get_config() -> Config:
    return Config()
