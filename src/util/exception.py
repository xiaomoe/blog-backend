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
