from datetime import datetime
from typing import Self

from sqlmodel import Field, Index, col, select
from src.common.db import session
from werkzeug.security import check_password_hash, generate_password_hash

from .base import BaseSQLModel


class User(BaseSQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(max_length=20, index=True)
    mobile: str = Field(nullable=False, unique=True, index=True)
    password: str | None = None
    company: str | None = Field(default=None, max_length=50)
    career: str | None = Field(default=None, max_length=50)
    home_url: str | None = Field(default=None, max_length=100)
    slogan: str | None = Field(default=None, max_length=200)
    avatar: str | None = Field(default=None)
    github: str | None = Field(default=None)
    email: str | None = Field(default=None, unique=True, nullable=True)
    status: int = Field(default=0, description="状态，0-正常，1-未激活，2-禁言，3-拉黑")
    last_login: datetime = Field(default_factory=datetime.now)
    is_deleted: bool = Field(default=0, description="是否删除")

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
            group_ids = session.exec(statement).all()
            # 查找分组的所有权限 名称
            statement = (
                select(Permission.name)
                .join(GroupPermission, GroupPermission.permission_id == Permission.id)
                .where(col(GroupPermission.group_id).in_(group_ids))
            )
            has_permission_name = session.exec(statement).all()  # 用户拥有的权限
            if has_permission_name and (auth in has_permission_name):
                return True
            return False

    def is_admin(self) -> bool:
        with session:
            statement = select(GroupUser.group_id).where(GroupUser.user_id == self.id)
            group_ids = session.exec(statement).all()
            if 1 in group_ids:  # TODO: admin group 是否存在
                return True
            return False

    def is_auth(self) -> bool:
        with session:
            statement = select(GroupUser.group_id).where(GroupUser.user_id == self.id)
            group_ids = session.exec(statement).all()
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
        one = session.exec(cls.username == username).first()
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

    def has_permission(self, meta: "PermissionMeta") -> bool:
        return True


class Group(BaseSQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=20, nullable=False, description="分组名称")
    info: str | None = Field(default=None)


class Permission(BaseSQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=32, nullable=False, description="权限名称")
    module: str = Field(max_length=20, nullable=False, description="所属权限模块")
    info: str | None = Field(default=None)

    __table_args__ = (Index("name_module", "name", "module", unique=True),)


class GroupUser(BaseSQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    group_id: int
    user_id: int

    __table_args__ = (Index("user_id_group_id", "user_id", "group_id"),)


class GroupPermission(BaseSQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    group_id: int
    permission_id: int

    __tableargs__ = (Index("group_id_permission_id", "group_id", "permission_id", unique=True),)


class Log(BaseSQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int
    username: str
    message: str
    path: str
    method: str
    create_time: int
    source: str  # func_name? data name?
