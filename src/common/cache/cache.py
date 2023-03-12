from datetime import timedelta
from typing import TypeVar

from pydantic.main import BaseModel

from .model import BaseNode

T = TypeVar("T", bound=BaseModel)


def get(node: BaseNode) -> BaseNode | None:
    data = node.Meta.storage.get(node._full_key())
    if data is not None:
        data = node.Meta.serializer.loads(data)
        return node.parse_obj(data)
    # 从源获取
    result = node.load()
    if result is not None:
        new_node = node.parse_obj(result)
        set(new_node)
        return new_node
    # TODO: 没有查到数据 处理缓存穿透
    return None


def set(node: BaseNode, ttl: timedelta | None = None) -> None:
    delta = ttl if ttl is not None else node.Meta.ttl
    data = node.Meta.serializer.dumps(node)
    node.Meta.storage.set(node._full_key(), data, delta)


def delete(node: BaseNode) -> None:
    """删除缓存."""
    node.Meta.storage.delete(node._full_key())


def refresh(node: BaseNode) -> BaseModel | None:
    """刷新缓存."""
    delete(node)
    return get(node)
