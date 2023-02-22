from typing import Any

from flask import Flask

from src.config import config

from .app import APIException, APIFlask, db, redis


def create_app() -> Flask:
    app = APIFlask(__name__)

    app.config.from_object(config)

    @app.get("/")
    def index() -> dict[str, Any]:
        with db.connect() as conn:
            print(conn)
        redis.set("a", 1)
        print(redis.get("a"))

        class NotFound(APIException):
            code: int = 404
            message: str = "Not Found."

        raise NotFound
        return {"msg": "Hello World"}

    return app
