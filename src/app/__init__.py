from typing import Any

from flask import Flask


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/")
    def index() -> dict[str, Any]:
        return {"msg": "Hello World!"}

    return app
