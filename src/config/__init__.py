from pathlib import Path

from pydantic import BaseSettings


class BaseConfig(BaseSettings):
    BASE_DIR: Path | str = Path(__file__).parent.parent

    SECRET_KEY: str = "123456"
    SQLALCHEMY_DATABASE_URI: str = ""
    REDIS_URL: str = "redis://localhost:6379/0"

    # qcloud 腾讯 cos 设置
    COS_SECRET_ID: str = ""
    COS_SECRET_KEY: str = ""
    COS_BUCKET: str = ""
    COS_REGION: str = ""

    # log
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file: str = ".env"


config: BaseConfig = BaseConfig()
