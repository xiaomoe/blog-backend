from typing import Any

import structlog
from flask import Flask

from src.common.auth import Auth, admin_required, permission_meta, permission_metas
from src.common.cos import cos
from src.common.log.flask_log import FlaskLogger
from src.config import config
from src.util.validation import body, parameter

from .app import APIFlask
from .cli import regsiter_cli
from .model import User

logger = structlog.get_logger("api.error")


def create_app() -> Flask:
    app = APIFlask(__name__)
    Auth(app, User)
    # 初始化后就加载 logger
    FlaskLogger(app)

    app.config.from_object(config)
    regsiter_cli(app)

    from pydantic import BaseModel

    class Page(BaseModel):
        page: int = 0
        count: int = 10

    class UserIn(BaseModel):
        name: str

    @app.post("/")
    @permission_meta("查看用户")
    @parameter(Page)
    @body(UserIn)
    def index(user: UserIn, page: Page) -> dict[str, Any]:
        return {
            "user": user,
            "page": page,
        }

    @app.get("/")
    @permission_meta("获取 cos")
    @admin_required
    def index_get() -> dict[str, Any]:
        logger.error("test from structlog")
        app.logger.error("from flask.logger")
        return cos.get_credential()

    @app.get("/permissions")
    @permission_meta("获取所有权限")
    def get_permissions() -> list[Any]:
        return list(permission_metas)

    return app
