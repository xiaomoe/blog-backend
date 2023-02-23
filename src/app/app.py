import os
import typing as t
from dataclasses import asdict, dataclass

import orjson
from flask import Flask
from flask.json.provider import JSONProvider
from flask.typing import ResponseReturnValue
from flask.wrappers import Response
from redis import Redis
from sqlalchemy import create_engine
from werkzeug.exceptions import HTTPException

from src.config import config

redis = Redis.from_url(config.REDIS_URL)
db = create_engine(config.SQLALCHEMY_DATABASE_URI, echo=True)


@t.runtime_checkable
class ToDictLike(t.Protocol):
    def dict(self) -> dict[str, t.Any]:
        ...


@t.runtime_checkable
class ToAsDictLike(t.Protocol):
    def as_dict(self) -> dict[str, t.Any]:
        ...


@dataclass
class APIException(Exception):
    code: int = 500
    error_code: int = 10000
    message: str = "内部错误"

    # def __init__(self, code: int | None = None, error_code: int | None = None, message: str | None = None) -> None:
    #     if code is not None:
    #         self.code = code
    #     if error_code is not None:
    #         self.error_code = error_code
    #     if message is not None:
    #         self.message = message
    #     super().__init__()

    def dict(self) -> dict[str, t.Any]:
        return {
            "code": self.code,
            "error_code": self.error_code,
            "message": self.message,
        }


class OrJSONProvider(JSONProvider):
    """替换 Flask 内部 JSON Provider 为 OrJson

    Args:
        JSONProvider (flask.json.provider.JSONProvider): internal json
    """

    def dumps(self, obj: t.Any, **kwargs: t.Any) -> str:
        try:
            res = orjson.dumps(obj)
        except Exception:
            # deal with other type
            if isinstance(obj, ToDictLike):
                res = orjson.dumps(obj.dict())
            if isinstance(obj, ToAsDictLike):
                res = orjson.dumps(obj.as_dict())
            raise
        return res.decode()

    def loads(self, s: str | bytes, **kwargs: t.Any) -> t.Any:
        return orjson.loads(s)


class APIFlask(Flask):
    json_provider_class = OrJSONProvider

    def __init__(
        self,
        import_name: str,
        static_url_path: str | None = None,
        static_folder: str | os.PathLike[str] | None = "static",
        static_host: str | None = None,
        host_matching: bool = False,
        subdomain_matching: bool = False,
        template_folder: str | os.PathLike[str] | None = "templates",
        instance_path: str | None = None,
        instance_relative_config: bool = False,
        root_path: str | None = None,
    ) -> None:
        super().__init__(
            import_name,
            static_url_path,
            static_folder,
            static_host,
            host_matching,
            subdomain_matching,
            template_folder,
            instance_path,
            instance_relative_config,
            root_path,
        )
        self.register_error_handler(HTTPException, self.error_handler_http)
        self.register_error_handler(APIException, self.error_handler_api)

    def make_response(self, rv: ResponseReturnValue) -> Response:
        """change to json Response"""
        if isinstance(rv, tuple):
            data, *other = rv
            rv = self.json.response(data), *other  # type: ignore
        elif not isinstance(rv, Response):
            rv = self.json.response(rv)

        return super().make_response(rv)

    @staticmethod
    def error_handler_http(error: HTTPException) -> ResponseReturnValue:
        if error.code:
            return {
                "code": error.code,
                "error_code": 999,
                "message": error.description,
            }, error.code
        return {
            "code": error.code,
            "error_code": 999,
            "message": error.description,
        }

    @staticmethod
    def error_handler_api(error: APIException) -> ResponseReturnValue:
        return asdict(error), error.code
