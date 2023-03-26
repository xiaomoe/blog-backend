from collections.abc import Sequence
from datetime import date, datetime
from typing import TYPE_CHECKING, Self

from sqlalchemy import BigInteger, Date, Index, SmallInteger, String, select
from sqlalchemy.orm import Mapped, mapped_column
from src.app.model.base import BaseModel, T_create_time, T_id, T_update_time
from src.common.db import session
from werkzeug.security import check_password_hash, generate_password_hash

if TYPE_CHECKING:

    from src.common.auth.permission import PermissionMeta


class User(BaseModel):
    id: Mapped[T_id] = mapped_column(init=False)
    username: Mapped[str] = mapped_column(String(32), index=True)
    mobile: Mapped[str] = mapped_column(unique=True, index=True)
    password: Mapped[str] = mapped_column(init=False)
    role_id: Mapped[int] = mapped_column(BigInteger, default=1)
    signature: Mapped[str] = mapped_column(String(200), default=None)
    avatar: Mapped[str] = mapped_column(String(255), default=None)
    email: Mapped[str | None] = mapped_column(default=None, unique=True)
    last_login: Mapped[datetime] = mapped_column(default_factory=datetime.now)
    status: Mapped[int] = mapped_column(default=0, comment="状态: 0-正常, 1-未激活, 2-禁言, 3-拉黑")
    is_deleted: Mapped[int] = mapped_column(SmallInteger, default=0, comment="是否删除: 0-未删除, 1-已删除")
    gender: Mapped[int] = mapped_column(SmallInteger, default=0, comment="性别: 0-未设置, 1-女, 2-男")
    birthday: Mapped[date] = mapped_column(Date, default=datetime.today)
    address: Mapped[str] = mapped_column(String(100), default="", comment="所在地")
    company: Mapped[str] = mapped_column(String(50), default="")
    career: Mapped[str] = mapped_column(String(50), default="")
    home_url: Mapped[str] = mapped_column(String(100), default="")
    github: Mapped[str] = mapped_column(default=None)
    create_time: Mapped[T_create_time] = mapped_column(default=None)
    update_time: Mapped[T_update_time] = mapped_column(default=None)

    __table_args__ = (Index("username_del", "username", "is_deleted", unique=True),)

    def get_primary_value(self) -> str:
        """获得主键值."""
        return str(self.id)

    def check_password(self, data: str) -> bool:
        return check_password_hash(self.password, data)  # type: ignore

    @classmethod
    def validate(cls, username: str, password: str) -> Self | None:
        """验证用户是否存在和密码是否正确."""
        one = cls.get_model_by_attr(username=username)
        if one and one.check_password(password):
            return one
        return None

    @classmethod
    def get_instance_by_primary(cls, value: str) -> Self | None:
        """根据主键获取实例."""
        return session.get(cls, int(value))

    def is_admin(self) -> bool:
        with session:
            statement = select(Role).where(Role.id == self.role_id)
            role = session.scalar(statement)
            if role and role.id == 1:  # NOTE: Admin id is 1
                return True
            return False

    def has_permission(self, meta: "PermissionMeta") -> bool:
        if self.is_admin():
            return True
        with session:
            # 查找用户所属分组 id
            role_statement = select(Role).where(Role.id == self.role_id)
            role = session.scalar(role_statement)
            if role is None:
                return False
            # 查找分组的所有权限 名称
            permission_statement = (
                select(Permission.name, Permission.module)
                .join(RolePermission, Permission.id == RolePermission.permission_id)
                .where(RolePermission.role_id == role.id)
            )

            existed_permissions = session.scalars(permission_statement).all()  # 用户拥有的权限
            return any(item.name == meta.auth and item.module == meta.module for item in existed_permissions)

    def set_password(self, data: str) -> None:
        """Password 需要 hash."""
        self.password = generate_password_hash(data)


class Role(BaseModel):
    id: Mapped[T_id] = mapped_column(init=False)
    name: Mapped[str] = mapped_column(String(32), index=True, comment="角色名称")
    info: Mapped[str | None] = mapped_column(String(255), default="")
    create_time: Mapped[T_create_time] = mapped_column(default=None)
    update_time: Mapped[T_update_time] = mapped_column(default=None)

    @property
    def permissions(self) -> Sequence["Permission"]:
        permission_statement = (
            select(Permission)
            .join(RolePermission, Permission.id == RolePermission.permission_id)
            .where(RolePermission.role_id == self.id)
        )

        return session.scalars(permission_statement).all()


class Permission(BaseModel):
    id: Mapped[T_id] = mapped_column(init=False)
    name: Mapped[str] = mapped_column(String(32), comment="权限名称")
    module: Mapped[str] = mapped_column(String(32), comment="权限所属模块")
    info: Mapped[str | None] = mapped_column(String(255), default="")
    create_time: Mapped[T_create_time] = mapped_column(default=None)
    update_time: Mapped[T_update_time] = mapped_column(default=None)

    __table_args__ = (Index("name_module", "name", "module", unique=True),)


class RolePermission(BaseModel):
    id: Mapped[T_id] = mapped_column(init=False)
    role_id: Mapped[int] = mapped_column(BigInteger)
    permission_id: Mapped[int] = mapped_column(BigInteger)
    create_time: Mapped[T_create_time] = mapped_column(default=None)

    __tableargs__ = (Index("group_id_permission_id", "group_id", "permission_id", unique=True),)


class Log(BaseModel):
    user_id: Mapped[int]
    username: Mapped[str]
    message: Mapped[str]
    path: Mapped[str]
    method: Mapped[str]
    create_time: Mapped[int]
    source: Mapped[str]  # func_name? data name?
