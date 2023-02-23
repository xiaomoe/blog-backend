from dataclasses import dataclass, field
from typing import Any

from src.app.app import APIException


@dataclass
class RequestParamsError(APIException):
    code: int = 422
    error_code: int = 10400
    message: str = "Parameters Error"
    detail: list[Any] = field(default_factory=list)
