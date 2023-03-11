from collections.abc import Callable
from functools import wraps
from typing import Any, Concatenate, ParamSpec, TypeVar

from flask import request
from pydantic import BaseModel, ValidationError

from src.util.exception import RequestParamsError

P = ParamSpec("P")
R = TypeVar("R")
S = TypeVar("S", bound=BaseModel)


def parameter(schema: type[S]) -> Callable[[Callable[Concatenate[S, P], R]], Callable[P, R]]:
    """Decorates a function to validate and convert query parameters.

    This decorator validates and converts query parameters using the provided schema.
    The schema should be a Pydantic model. If validation fails, a 422 status code is returned.
    If validation succeeds, the validated parameters are passed to the decorated function.

    Args:
        schema (BaseModel): A Pydantic model used to validate and convert query parameters.

    Returns:
        A decorator function that can be applied to other functions.

    Examples:
        >>> class Page(BaseModel):
        ...     page: int
        ...     count: int
        >>> @app.route('/')
        ... @parameter(Page)
        ... def index(page: Page) -> list[str]:
        ...     ...

    Notes:
        - 函数参数顺序要满足装饰器顺序
    """

    def decorator_parameter(func: Callable[Concatenate[S, P], R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper_parameter(*args: P.args, **kwargs: P.kwargs) -> R:
            # Validate and convert query parameters using the provided schema
            try:
                data = schema.validate(request.args.to_dict())
            except ValidationError as e:
                raise RequestParamsError(detail=e.errors()) from None
            return func(data, *args, **kwargs)

        return wrapper_parameter

    return decorator_parameter


def body(schema: type[S]) -> Callable[[Callable[Concatenate[S, P], R]], Callable[P, R]]:
    """Decorates a function to validate and convert request json.

    Args:
        schema (BaseModel): A Pydantic model used to validate and convert json.

    Returns:
        A decorator function that can be applied to other functions.

    Examples:
        >>> @app.route('/', methods=['POST'])
        ... @body(BaseModel)
        ... def index():
        ...     ...

    Notes:
        - 函数参数顺序要满足装饰器顺序
    """

    def decorator_body(func: Callable[Concatenate[S, P], R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper_body(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                _data: dict[str, Any] = request.get_json(silent=True) or {}
                data = schema.validate(_data)
            except ValidationError as e:
                raise RequestParamsError(detail=e.errors()) from None
            return func(data, *args, **kwargs)

        return wrapper_body

    return decorator_body
