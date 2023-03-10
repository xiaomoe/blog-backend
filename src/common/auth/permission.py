from collections.abc import Callable
from dataclasses import dataclass, field
from functools import wraps
from typing import ParamSpec, TypeVar

from src.util.exception import Forbidden, Unauthorization

from .auth import current_user

P = ParamSpec("P")
R = TypeVar("R")


@dataclass(slots=True, eq=True, order=True)
class PermissionMeta:
    """Dataclass representing Permission metadata.

    Attributes:
        module (str): Module to which permission belongs.
        auth (str): Type of authorization (i.e can read, can write etc).

    """

    module: str
    auth: str
    info: str = field(default="", compare=False)

    def __hash__(self) -> int:
        return id((self.module, self.auth))


# 收集的函数权限 用于注册到数据库
permission_metas: set[PermissionMeta] = set()


def permission_meta(
    auth: str, module: str = "common", required: bool = False
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator for adding Permission Metadata to a method.

    Args:
        auth (str): Type of authorization (i.e. can read, can write).
        module (str, optional): Module name. Defaults to "common".
        required (bool): 是否作为权限验证. Defaults to False.

    Returns:
        Callable: decorated function

    Examples:
        >>> @app.post('/comment')
        >>> @permission_meta(auth='增加用户', module='用户')
        >>> @body(BaseModel)
        >>> def index():
        ...     ...

    """

    def decorator_permission(func: Callable[P, R]) -> Callable[P, R]:
        # 收集权限信息 用于后面添加到数据库 permission 表中
        func_name = func.__module__ + "." + func.__qualname__
        meta = PermissionMeta(module, auth, func_name)
        permission_metas.add(meta)
        if required:

            @wraps(func)
            def wrapper_permission(*args: P.args, **kwargs: P.kwargs) -> R:
                # 请求进来时验证权限
                user = current_user.get()
                if user is None:
                    raise Unauthorization()
                if not user.has_permission(meta):
                    raise Forbidden()
                return func(*args, **kwargs)

            return wrapper_permission
        return func

    return decorator_permission


def admin_required(func: Callable[P, R]) -> Callable[P, R]:
    """管理员权限验证"""

    @wraps(func)
    def wrapper_admin_required(*args: P.args, **kwargs: P.kwargs) -> R:
        user = current_user.get()
        print(user)
        if user is None:
            raise Unauthorization(message="请登录")
        if not user.is_admin():
            raise Forbidden(message="需要管理员权限")
        return func(*args, **kwargs)

    return wrapper_admin_required


def login_required(
    func: Callable[P, R] | None = None, *, optional: bool = False
) -> Callable[[Callable[P, R]], Callable[P, R]] | Callable[P, R]:
    def decorator_login_required(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper_login_required(*args: P.args, **kwargs: P.kwargs) -> R:
            user = current_user.get()
            if not optional and user is None:
                raise Unauthorization()
            return func(*args, **kwargs)

        return wrapper_login_required

    if func is not None:
        return decorator_login_required(func)

    return decorator_login_required
