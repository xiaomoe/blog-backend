from flask import Blueprint
from sqlmodel import col, or_, select
from src.common.auth import current_user, login_required
from src.common.auth.auth import JWTToken
from src.common.db import session
from src.common.redis import redis
from src.util.exception import Created, ParameterError, Updated
from src.util.validation import body, parameter

from app.model.user import Group, GroupPermission, GroupUser, Permission, User
from app.schema.user import (
    ChangePasswordSchema,
    LoginSchema,
    ResetPasswordSchema,
    ResigerSchema,
    UsernameSchema,
    UserUpdateSchema,
)

bp = Blueprint("user", __name__, url_prefix="/user")


@bp.route("/username-check", methods=["GET"])
@parameter(UsernameSchema)
def check_username(params: UsernameSchema):
    """验证是否合法用户名"""
    existed = User.get_model_by_attr(username=params.username)
    return {"is_valid": not existed}


@bp.route("/register", methods=["POST"])
@body(ResigerSchema)
def register(body: ResigerSchema):
    # 验证验证码是否正确
    # 用户名是否已经存在
    # 手机号是否已经存在
    code = redis.get(f"1:{body.mobile}") or b""
    if body.code != code:
        raise ParameterError(message="验证码不正确，请重试")
    with session:
        existed = session.exec(
            select(User).where(or_(col(User.username) == body.username, col(User.mobile) == body.mobile))
        ).first()
        if existed:
            raise ParameterError(message="用户名或手机号已存在，请更换")
        user = User(username=body.username, mobile=body.mobile)
        user.set_password(body.password)
        user.save()
        GroupUser(group_id=2, user_id=user.id)  # type:ignore
        session.commit()
    return Created(message="创建用户成功")


@bp.route("/login", methods=["POST"])
@body(LoginSchema)
def login(body: LoginSchema):
    """手机号密码登陆"""
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


@bp.route("/info", methods=["PUT"])
@login_required
@body(UserUpdateSchema)
# @permission(auth="修改个人信息", module="user")
def change_info(body: UserUpdateSchema):
    """修改个人信息"""
    user = current_user.get()
    user.update(body)
    user.save()
    return Updated(message="用户信息更新成功")


@bp.route("/change-password", methods=["POST"])
@login_required
@body(ChangePasswordSchema)
def change_password(body: ChangePasswordSchema):
    """修改密码"""
    user = current_user.get()
    if not user.check_password(body.old_password):
        raise ParameterError(message="密码错误")
    user.set_password(body.password)
    user.save()

    return Updated(message="修改密码成功")


@bp.route("/reset-password", methods=["POST"])
@body(ResetPasswordSchema)
def reset_password(body: ResetPasswordSchema):
    """重置密码"""
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
    return Updated(message="重置密码成功")


@bp.route("/info", methods=["GET"])
@login_required
def get_self_info():
    """获得自己的信息"""
    user = current_user.get()
    with session:
        groups = session.exec(
            select(col(Group.id), col(Group.name))  # type: ignore
            .join(GroupUser, Group.id == GroupUser.group_id)
            .where(GroupUser.user_id == user.id)
        ).all()
        data = user.dict(
            exclude={
                "password",
                "is_deleted",
                "last_login",
                "status",
            }
        )
        data["groups"] = groups
        # 获得权限列表
        permissions = session.exec(
            select(Permission.name)
            .join(GroupPermission, Permission.id == GroupPermission.permission_id)
            .where(col(GroupPermission.group_id).in_([item[0] for item in groups]))
        ).all()
        data["permissions"] = permissions  # 用户权限
        return data
