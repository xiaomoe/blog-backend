from os import PathLike
from pathlib import Path

from pydantic import BaseSettings


class BaseConfig(BaseSettings):
    BASE_DIR: PathLike[str] | str = Path(__file__).parent.parent

    SECRET_KEY: str = "123456"
    SQLALCHEMY_DATABASE_URI: str = ""
    REDIS_URL: str = "redis://localhost:6379/0"

    class Config:
        env_file: str = ".env"


config: BaseConfig = BaseConfig()
