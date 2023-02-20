from redis import Redis
from sqlalchemy import create_engine

from src.config import config

redis = Redis.from_url(config.REDIS_URL)
db = create_engine(config.SQLALCHEMY_DATABASE_URI, echo=True)
