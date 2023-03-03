from typing import Any

import structlog
from flask import Flask

from src.common.cos import cos
from src.common.log.flask_log import FlaskLogger
from src.config import config
from src.util.validation import body, parameter

from .app import APIFlask
from .cli import regsiter_cli

logger = structlog.get_logger("api.error")


def create_app() -> Flask:
    app = APIFlask(__name__)
    FlaskLogger(app)

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
        logger.error("test from structlog")
        app.logger.error("from flask.logger")
        return cos.get_credential()

    return app
