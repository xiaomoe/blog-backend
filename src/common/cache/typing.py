from datetime import timedelta
from typing import Any, Protocol, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class Storage(Protocol):
    def connect(self) -> None:
        ...

    def close(self) -> None:
        ...

    def get(self, key: str) -> Any:
        ...

    def set(self, key: str, value: Any, ttl: timedelta | None = None) -> None:
        ...

    def delete(self, key: str) -> None:
        ...

    def exists(self, key: str) -> bool:
        ...


class Serializer(Protocol):
    def dumps(self, obj: Any) -> bytes:
        ...

    def loads(self, blob: bytes) -> Any:
        ...
