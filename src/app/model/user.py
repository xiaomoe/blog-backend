from datetime import datetime
from typing import Any, Self

from sqlalchemy import Index, String, select
from sqlalchemy.orm import Mapped, mapped_column
from src.app.model.base import BaseModel
from src.common.db import session
from werkzeug.security import check_password_hash, generate_password_hash


class User(BaseModel):
    username: Mapped[str] = mapped_column(max_length=20, index=True)
    mobile: Mapped[str] = mapped_column(nullable=False, unique=True, index=True)
    password: Mapped[str] = mapped_column(init=False)
    company: Mapped[str] = mapped_column(default=None, max_length=50)
    career: Mapped[str] = mapped_column(default=None, max_length=50)
    home_url: Mapped[str] = mapped_column(default=None, max_length=100)
    slogan: Mapped[str] = mapped_column(default=None, max_length=200)
    avatar: Mapped[str] = mapped_column(default=None)
    github: Mapped[str] = mapped_column(default=None)
    email: Mapped[str] = mapped_column(default=None, unique=True, nullable=True)
    status: Mapped[int] = mapped_column(default=0, comment="状态: 0-正常, 1-未激活, 2-禁言, 3-拉黑")
    last_login: Mapped[datetime] = mapped_column(default_factory=datetime.now)
    is_deleted: Mapped[int] = mapped_column(default=0, comment="是否删除")

    __table_args__ = (Index("username_del", "username", "is_deleted", unique=True),)

    def set_password(self, data: str) -> None:
        self.password = generate_password_hash(data)

    def check_password(self, data: str) -> bool:
        return check_password_hash(self.password, data)  # type: ignore

    def check_permission(self, auth: str, module: str) -> bool:
        if self.is_admin():
            return True
        with session:
            # 查找用户所属分组 id
            statement = select(GroupUser.group_id).where(GroupUser.user_id == self.id)
            group_ids = session.scalars(statement).all()
            # 查找分组的所有权限 名称
            statement = (
                select(Permission.name)  # type: ignore
                .join(GroupPermission, GroupPermission.permission_id == Permission.id)
                .where(GroupPermission.group_id.in_(group_ids))
            )
            has_permission_name = session.scalars(statement).all()  # 用户拥有的权限
            if has_permission_name and (auth in has_permission_name):  # type: ignore
                return True
            return False

    def is_admin(self) -> bool:
        with session:
            statement = select(GroupUser.group_id).where(GroupUser.user_id == self.id)
            group_ids = session.scalars(statement).all()
            if 1 in group_ids:  # TODO: admin group 是否存在
                return True
            return False

    def is_auth(self) -> bool:
        with session:
            statement = select(GroupUser.group_id).where(GroupUser.user_id == self.id)
            group_ids = session.scalars(statement).all()
            if 3 in group_ids:  # TODO: author group 是否存在
                return True
            return False

    def get_primary_value(self) -> str:
        return str(self.id)

    @classmethod
    def validate(cls, username: str, password: str) -> Self | None:  # type:ignore
        """验证用户是否存在和密码是否正确.

        Examples:
        >>> user = cls.get(username)
        >>> if user is None:
        ...     return None
        >>> return check_password(password, user.password)
        """
        one = cls.get_model_by_attr(username=username)
        if one:
            return one.check_password(password)
        return None

    @classmethod
    def get_instance_by_primary(cls, value: str) -> Self | None:
        """根据主键获取实例.

        Examples:
        >>> return cls.get(int(value))
        """
        return None  # TODO

    def has_permission(self, meta: Any) -> bool:
        return True


class Group(BaseModel):
    name: Mapped[str] = mapped_column(String(20), comment="分组名称")
    info: Mapped[str] = mapped_column(default=None)


class Permission(BaseModel):
    name: Mapped[str] = mapped_column(max_length=32, nullable=False, comment="权限名称")
    module: Mapped[str] = mapped_column(String(20), comment="所属权限模块")
    info: Mapped[str] = mapped_column(default=None)

    __table_args__ = (Index("name_module", "name", "module", unique=True),)


class GroupUser(BaseModel):
    group_id: Mapped[int]
    user_id: Mapped[int]

    __table_args__ = (Index("user_id_group_id", "user_id", "group_id"),)


class GroupPermission(BaseModel):
    group_id: Mapped[int]
    permission_id: Mapped[int]

    __tableargs__ = (Index("group_id_permission_id", "group_id", "permission_id", unique=True),)


class Log(BaseModel):
    user_id: Mapped[int]
    username: Mapped[str]
    message: Mapped[str]
    path: Mapped[str]
    method: Mapped[str]
    create_time: Mapped[int]
    source: Mapped[str]  # func_name? data name?
