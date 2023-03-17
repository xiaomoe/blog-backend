from datetime import timedelta
from pathlib import Path

from pydantic import BaseSettings


class BaseConfig(BaseSettings):
    BASE_DIR: Path | str = Path(__file__).parent.parent

    SECRET_KEY: str = "123456"
    SQLALCHEMY_DATABASE_URI: str
    SQLALCHEMY_POOL_SIZE: int = 10

    # redis
    REDIS_URL: str

    # qcloud 腾讯 cos 设置
    COS_SECRET_ID: str
    COS_SECRET_KEY: str
    COS_BUCKET: str
    COS_REGION: str

    # log
    LOG_LEVEL: str = "INFO"

    # secret
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRES_DELTA: timedelta = timedelta(hours=2)

    # redis

    class Config:
        env_file: str = ".env"


# https://github.com/pydantic/pydantic/issues/3753#issuecomment-1087417884
config: BaseConfig = BaseConfig.parse_obj({})
