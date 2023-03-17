from typing import Self, TypeVar

from pydantic import BaseModel
from sqlmodel import SQLModel, func, select
from src.common.db import session

TBaseSQLModel = TypeVar("TBaseSQLModel", bound="BaseSQLModel")


class BaseSQLModel(SQLModel):
    def save(self):
        """新增或修改时保存到数据库中
        e.g. user = User.from_orm(data).save()
        """
        with session:
            session.add(self)
            session.commit()
            session.refresh(self)
            return self

    @classmethod
    def get_model_by_id(cls, id: int) -> Self | None:
        """根据 id 获得 row"""
        with session:
            return session.get(cls, id)

    @classmethod
    def get_model_by_attr(cls, **kwargs) -> Self | None:
        """根据属性获得 row"""
        with session:
            return session.exec(select(cls).filter_by(**kwargs)).first()

    @classmethod
    def get_all(cls, page: int = 0, count: int = 10, **kwargs) -> list[Self]:
        with session:
            statement = select(cls).filter_by(**kwargs).offset(page * count).limit(count)
            return session.exec(statement).all()

    @classmethod
    def count(cls, **kwargs) -> int:
        with session:
            statement = select(func.count(cls.id)).filter_by(**kwargs)  # type: ignore
            result = session.execute(statement)
            return result.scalar() or 0

    def update(self, schema: BaseModel):
        # schema.from_orm(self)
        data = schema.dict(exclude_unset=True)
        # print(data)
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
