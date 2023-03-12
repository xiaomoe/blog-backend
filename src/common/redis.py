from redis import Redis

from src.config import config

redis = Redis.from_url(
    config.REDIS_URL,
    decode_responses=True,
)
