from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Any

from redis import Redis


class BaseStorage(ABC):
    @abstractmethod
    def connect(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    def close(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    def get(self, key: str) -> Any:
        raise NotImplementedError()

    @abstractmethod
    def set(self, key: str, value: Any, ttl: timedelta | None = None) -> None:
        raise NotImplementedError()

    @abstractmethod
    def delete(self, key: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def exists(self, key: str) -> bool:
        raise NotImplementedError()


class RedisStorage(BaseStorage):
    _redis: "Redis[bytes]"

    def __init__(self, url: str, pool_size: int = 100) -> None:
        self.url = url
        self.pool_size = pool_size
        self.connect()

    def connect(self) -> None:
        self._redis = Redis.from_url(self.url, max_connections=self.pool_size)

    def close(self) -> None:
        self._redis.close()

    def get(self, key: str) -> bytes | None:
        return self._redis.get(key)

    def set(self, key: str, value: Any, ttl: timedelta | None = None) -> None:
        self._redis.set(key, value, ex=ttl)

    def delete(self, key: str) -> None:
        self._redis.delete(key)

    def exists(self, key: str) -> bool:
        return bool(self._redis.exists(key))
