from __future__ import annotations

import re
from datetime import datetime
from typing import TYPE_CHECKING, Annotated, Any, Self

from sqlalchemy import BigInteger, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, declared_attr, mapped_column
from src.common.db import session

if TYPE_CHECKING:
    from collections.abc import Sequence


class Declarative(MappedAsDataclass, DeclarativeBase):
    """BaseModel 创建时(也就是 DeclarativeBase 子类化时)会创建 register(包括 metadata 和 mapper).

    之后它的子类会自动将它们自己(也就是 Table)通过它(BaseModel)的 register 属性注册到全局的 metadata 和 mapper.
    """


T_id = Annotated[int, mapped_column(BigInteger, primary_key=True)]  # bigint 类型主键
T_create_time = Annotated[datetime, mapped_column(insert_default=func.now())]
T_update_time = Annotated[datetime, mapped_column(onupdate=func.now())]
"""
create_time: Mapped[T_create_time] = mapped_column(default=None)
update_time: Mapped[T_update_time] = mapped_column(default=None)
"""


class BaseModel(Declarative):

    __abstract__ = True

    @declared_attr.directive
    @classmethod
    def __tablename__(cls) -> str:
        # 将大写字母替换为下划线加小写字母
        result = re.sub(r"[A-Z]", lambda x: f"_{x.group(0).lower()!r}", cls.__tablename__)
        # 去掉首个下划线
        result = result.lstrip("_")
        return result

    id: Mapped[T_id] = mapped_column(init=False)

    def save(self) -> Self:
        """新增或修改时保存到数据库中."""
        with session:
            session.add(self)
            session.commit()
            session.refresh(self)
            return self

    @classmethod
    def get_model_by_id(cls, id: int) -> Self | None:
        """根据 id 获得 row."""
        with session:
            return session.get(cls, id)

    @classmethod
    def get_model_by_attr(cls, **kwargs: Any) -> Self | None:
        """根据属性获得 row."""
        with session:
            return session.scalars(select(cls).filter_by(**kwargs)).first()

    @classmethod
    def get_all(cls, page: int = 0, count: int = 10, **kwargs: Any) -> Sequence[Self]:
        with session:
            statement = select(cls).filter_by(**kwargs).offset(page * count).limit(count)
            return session.scalars(statement).all()

    @classmethod
    def count(cls, **kwargs: Any) -> int:
        with session:
            statement = select(func.count(cls.id)).filter_by(**kwargs)
            result = session.execute(statement)
            return result.scalar() or 0

    def update(self, data: dict[str, Any]) -> None:
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)


class User(BaseModel):
    pass
