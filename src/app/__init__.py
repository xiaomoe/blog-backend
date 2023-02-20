from typing import Any

from flask import Flask

from src.config import config

from .app import db, redis


def create_app() -> Flask:
    app = Flask(__name__)

    app.config.from_object(config)

    @app.get("/")
    def index() -> dict[str, Any]:
        with db.connect() as conn:
            print(conn)
        redis.set("a", 1)
        print(redis.get("a"))
        return {"msg": "Hello World"}

    return app
