from dataclasses import asdict

from flask import Blueprint
from flask.typing import ResponseValue
from sqlalchemy import or_, select
from src.common.auth import current_user, login_required
from src.common.auth.auth import JWTToken
from src.common.db import session
from src.common.redis import redis
from src.util.exception import Created, ParameterError, Updated
from src.util.validation import body, parameter

from app.model.user import Role, User
from app.schema.user import (
    ChangePasswordSchema,
    LoginSchema,
    ResetPasswordSchema,
    ResigerSchema,
    UsernameSchema,
    UserUpdateSchema,
)

bp = Blueprint("user", __name__, url_prefix="/user")


@bp.get("/username-check")
@parameter(UsernameSchema)
def check_username(params: UsernameSchema) -> ResponseValue:
    """验证是否合法用户名."""
    existed = User.get_model_by_attr(username=params.username)
    return {"is_valid": not existed}


@bp.post("/register")
@body(ResigerSchema)
def register(body: ResigerSchema) -> ResponseValue:
    # 验证验证码是否正确
    # 用户名是否已经存在
    # 手机号是否已经存在
    code = redis.get(f"1:{body.mobile}") or b""
    if body.code != code:
        raise ParameterError(message="验证码不正确 请重试")
    with session:
        existed = session.scalar(
            select(User).where(or_((User.username) == body.username, (User.mobile) == body.mobile))
        )
        if existed:
            raise ParameterError(message="用户名或手机号已存在 请更换")
        user = User(username=body.username, mobile=body.mobile)
        user.set_password(body.password)
        user.save()
        session.commit()
    return Created(message="创建用户成功").to_dict()


@bp.post("/login")
@body(LoginSchema)
def login(body: LoginSchema) -> ResponseValue:
    """手机号密码登陆."""
    user = User.get_model_by_attr(mobile=body.mobile)
    if user is None:
        raise ParameterError(message="手机号密码错误")
    if body.type == 1:
        # 手机号密码
        if not user.check_password(body.password):
            raise ParameterError(message="手机号密码错误")
    else:
        # 手机号验证码
        code = redis.get(f"2:{body.mobile}") or ""
        if body.password != code:
            raise ParameterError(message="验证码错误")
    return {"token": JWTToken.encode_token({"sub": str(user.id)})}


@bp.put("/info")
@login_required
@body(UserUpdateSchema)
# @permission(auth="修改个人信息", module="user")
def change_info(body: UserUpdateSchema) -> ResponseValue:
    """修改个人信息."""
    user = current_user.get()
    user.update(body.dict())
    user.save()
    return Updated(message="用户信息更新成功").to_dict()


@bp.post("/change-password")
@login_required
@body(ChangePasswordSchema)
def change_password(body: ChangePasswordSchema) -> ResponseValue:
    """修改密码."""
    user = current_user.get()

    if not user.check_password(body.old_password):
        raise ParameterError(message="密码错误")
    user.set_password(body.password)
    user.save()

    return Updated(message="修改密码成功").to_dict()


@bp.post("/reset-password")
@body(ResetPasswordSchema)
def reset_password(body: ResetPasswordSchema) -> ResponseValue:
    """重置密码."""
    # 手机号是否已注册
    # code 是否正确
    # 重置密码
    user = User.get_model_by_attr(mobile=body.mobile)
    if user is None:
        raise ParameterError(message="手机号不存在")
    code = redis.get(f"4:{body.mobile}") or ""
    if body.code != code:
        raise ParameterError(message="验证码错误")
    user.set_password(body.password)
    user.save()
    return Updated(message="重置密码成功").to_dict()


@bp.get("/info")
@login_required
def get_self_info() -> ResponseValue:
    """获得自己的信息."""
    user = current_user.get()
    with session:
        role = session.scalar(select(Role).where(Role.id == user.role_id))
        data = asdict(user)
        data.pop("password")
        if role:
            data["role"] = role
            data["permissions"] = role.permissions
        return data
