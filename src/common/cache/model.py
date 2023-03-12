from datetime import timedelta
from typing import Any, TypeVar

import orjson
from pydantic import BaseModel

from .typing import Serializer, Storage

T = TypeVar("T", bound=BaseModel)


class JSONSerializer:
    def dumps(self, obj: Any) -> bytes:
        return orjson.dumps(obj, default=self.default)

    def loads(self, blob: bytes) -> Any:
        return orjson.loads(blob)

    @staticmethod
    def default(obj: Any) -> Any:
        if hasattr(obj, "dict"):
            res = obj.dict()
        elif hasattr(obj, "as_dict"):
            res = obj.as_dict()
        else:
            raise RuntimeError(f"{obj}类型不支持 JSON 化")
        return res


class BaseNode(BaseModel):
    id: int
    username: str | None = None
    age: int | None = None

    def _full_key(self) -> str:
        return self.Meta.prefix + self.key()

    def key(self) -> str:
        raise NotImplementedError()

    def load(self) -> Any:
        raise NotImplementedError()

    class Meta:
        ttl: timedelta | None = None
        prefix: str = ""
        serializer: Serializer = JSONSerializer()
        storage: Storage
