from typing import Any

from pydantic import BaseModel, validator

from .common import validate_mobile, validate_password, validate_username


class CodeSchema(BaseModel):
    mobile: str
    type: int

    _mobile = validator("mobile", allow_reuse=True)(validate_mobile)

    @validator("type")
    def validate_type(cls, val: Any) -> Any:  # noqa:N805
        if val > 4 or val < 1:
            raise ValueError("只能在1, 2, 3, 4中选择")
        return val


class ResigerSchema(BaseModel):
    mobile: str
    username: str
    password: str
    password2: str
    code: str

    _mobile = validator("mobile", allow_reuse=True)(validate_mobile)
    _password = validator("password", allow_reuse=True)(validate_password)
    _username = validator("username", allow_reuse=True)(validate_username)

    @validator("password2")
    def check_password2(cls, val: Any, values: Any, **kwargs: Any) -> Any:  # noqa:N805
        if "password" in values and val != values["password"]:
            raise ValueError("两次密码不一致")
        return val

    @validator("code")
    def check_code(cls, v: Any, values: Any) -> Any:  # noqa:N805
        if len(v) != 4 or (not v.isdigit()):
            raise ValueError("验证码不正确")
        return v


class UsernameSchema(BaseModel):
    username: str
    _username = validator("username", allow_reuse=True)(validate_username)


class LoginSchema(BaseModel):
    mobile: str
    type: int
    password: str  # 密码或验证码

    _mobile = validator("mobile", allow_reuse=True)(validate_mobile)


class UserUpdateSchema(BaseModel):
    username: str | None = None
    company: str | None = None
    career: str | None = None
    home_url: str | None = None
    slogan: str | None = None
    avatar: str | None = None
    github: str | None = None
    email: str | None = None


class ChangePasswordSchema(BaseModel):
    password: str
    password2: str
    old_password: str
    _password = validator("password", allow_reuse=True)(validate_password)

    @validator("password2")
    def check_password2(cls, val: Any, values: Any, **kwargs: Any) -> Any:  # noqa:N805
        if "password" in values and val != values["password"]:
            raise ValueError("两次密码不一致")


class ResetPasswordSchema(BaseModel):
    mobile: str
    password: str
    password2: str
    code: str

    _mobile = validator("mobile", allow_reuse=True)(validate_mobile)
    _password = validator("password", allow_reuse=True)(validate_password)

    @validator("password2")
    def check_password2(cls, val: Any, values: Any, **kwargs: Any) -> Any:  # noqa:N805
        if "password" in values and val != values["password"]:
            raise ValueError("两次密码不一致")

    @validator("code")
    def check_code(cls, v: Any, values: Any) -> Any:  # noqa:N805
        if len(v) != 4 or (not v.isdigit()):
            raise ValueError("验证码不正确")
        return v
