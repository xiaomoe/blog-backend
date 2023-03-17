from dataclasses import dataclass, field
from typing import Any

from src.app.app import APIException


@dataclass
class RequestParamsError(APIException):
    code: int = 422
    error_code: int = 10422
    message: str = "Parameters Error"
    detail: list[Any] = field(default_factory=list)


@dataclass
class Forbidden(APIException):
    code: int = 403
    error_code: int = 10403
    message: str = "Forbidden"


@dataclass
class Unauthorization(APIException):
    code: int = 401
    error_code: int = 10401
    message: str = "Unautorization"


class Success(APIException):
    code: int = 200
    message: str = "Ok"
    error_code: int = 0


class Created(APIException):
    code: int = 201
    message: str = "创建成功"
    error_code: int = 1


class Updated(APIException):
    code: int = 200
    message: str = "更新成功"
    error_code: int = 2


class Deleted(APIException):
    code: int = 200
    message: str = "删除成功"
    error_code: int = 3


class Unautorization(APIException):
    code: int = 401
    message: str = "需要登录"
    error_code: int = 10010


class NotFound(APIException):
    code: int = 404
    message: str = "资源不存在"
    error_code: int = 10030


class ParameterError(APIException):
    code: int = 400
    message: str = "参数错误"
    error_code: int = 10040


class ServerError(APIException):
    code: int = 500
    message: str = "内部错误"
    error_code: int = 999
