from typing import Any

from flask import Flask

from src.common.cos import cos
from src.config import config
from src.util.validation import body, parameter

from .app import APIFlask
from .cli import regsiter_cli


def create_app() -> Flask:
    app = APIFlask(__name__)

    app.config.from_object(config)
    regsiter_cli(app)

    from pydantic import BaseModel

    class Page(BaseModel):
        page: int = 0
        count: int = 10

    class User(BaseModel):
        name: str

    @app.post("/")
    @parameter(Page)
    @body(User)
    def index(user: User, page: Page) -> dict[str, Any]:
        return {
            "user": user,
            "page": page,
        }

    @app.get("/")
    def index_get() -> dict[str, Any]:
        return cos.get_credential()

    return app
