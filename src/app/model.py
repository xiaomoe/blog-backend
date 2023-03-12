from typing import TYPE_CHECKING, Self

from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, MappedColumn, mapped_column

if TYPE_CHECKING:
    from src.common.auth.permission import PermissionMeta


class BaseModel(DeclarativeBase):
    pass


class User(BaseModel):
    __tablename__ = "user"
    id: MappedColumn[int] = mapped_column(primary_key=True, autoincrement=True, comment="主键")
    username: MappedColumn[str] = mapped_column(String(255), unique=True, nullable=False)
    password: MappedColumn[str] = mapped_column(String(255))

    def get_primary_value(self) -> str:
        return str(self.id)

    @classmethod
    def validate(cls, username: str, password: str) -> Self | None:
        """验证用户是否存在和密码是否正确.

        Examples:
        >>> user = cls.get(username)
        >>> if user is None:
        ...     return None
        >>> return check_password(password, user.password)
        """
        return cls(id=1, username="test")

    @classmethod
    def get_instance_by_primary(cls, value: str) -> Self | None:
        """根据主键获取实例.

        Examples:
        >>> return cls.get(int(value))
        """
        return cls(id=1, username="test")

    def is_admin(self) -> bool:
        return False

    def has_permission(self, meta: "PermissionMeta") -> bool:
        return True
