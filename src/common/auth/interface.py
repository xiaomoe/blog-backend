from abc import ABC, abstractclassmethod, abstractmethod
from typing import TYPE_CHECKING, Protocol, Self

from pydantic import BaseModel

if TYPE_CHECKING:
    from .permission import PermissionMeta


class User(Protocol):
    def get_primary_value(self) -> str:
        """获得主键值.

        Examples:
        >>> return str(self.id)
        """
        ...

    @classmethod
    def validate(cls, username: str, password: str) -> Self | None:  # noqa
        """验证用户是否存在和密码是否正确.

        Examples:
        >>> user = cls.get(username)
        >>> if user is None:
        ...     return None
        >>> return check_password(password, user.password)
        """
        ...

    @classmethod
    def get_instance_by_primary(cls, value: str) -> Self | None:  # noqa
        """根据主键获取实例.

        Examples:
        >>> return cls.get(int(value))
        """
        ...

    def is_admin(self) -> bool:
        ...

    def has_permission(self, meta: "PermissionMeta") -> bool:
        ...


class UserInter(ABC):
    @abstractmethod
    def get_primary_value(self) -> str:
        """获得主键值.

        Examples:
        >>> return str(self.id)
        """

    @abstractclassmethod
    def validate(cls, username: str, password: str) -> Self | None:  # noqa
        """验证用户是否存在和密码是否正确.

        Examples:
        >>> user = cls.get(username)
        >>> if user is None:
        ...     return None
        >>> return check_password(password, user.password)
        """

    @abstractclassmethod
    def get_instance_by_primary(cls, value: str) -> Self | None:  # noqa
        """根据主键获取实例.

        Examples:
        >>> return cls.get(int(value))
        """

    @abstractmethod
    def is_admin(self) -> bool:
        pass

    @abstractmethod
    def has_permission(self, meta: "PermissionMeta") -> bool:
        pass


class LoginScheme(BaseModel):
    username: str
    password: str
