from collections.abc import Callable
from typing import ParamSpec, TypeAlias, TypeVar

P = ParamSpec("P")
R = TypeVar("R")

Func: TypeAlias = Callable[P, R]
