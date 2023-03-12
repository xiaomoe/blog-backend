"""缓存.

Examples:
    from datetime import timedelta
    from typing import Any

    from src.common.cache import BaseNode, JSONSerializer, RedisStorage, cache

    storage = RedisStorage(url="redis://:123456@127.0.0.1:6379/0")


    class UserInfo(BaseNode):
        id: int
        username: str | None = None
        age: int | None = None

        def key(self) -> str:
            return str(self.id)

        def load(self) -> Any:
            return UserInfo(id=1, username="test")

        class Meta:
            prefix = "user:"
            ttl = timedelta(seconds=120)
            storage = storage
            serializer = JSONSerializer()


    t = cache.get(UserInfo(id=1))  # Get
    cache.set(UserInfo(id=2, username="222"))  # Set

"""
from . import cache
from .model import BaseNode, JSONSerializer
from .storage import RedisStorage

__all__ = (
    "RedisStorage",
    "cache",
    "BaseNode",
    "JSONSerializer",
)
