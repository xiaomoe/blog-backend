from typing import Any

import structlog
from flask import Flask

from src.common.auth import Auth
from src.common.log.flask_log import FlaskLogger
from src.common.search import es
from src.common.sock import sock
from src.config import config

from .app import APIFlask
from .cli import regsiter_cli
from .model.user import User

logger = structlog.get_logger("api.error")


def create_app() -> Flask:
    app = APIFlask(__name__)
    Auth(app, User)
    # 初始化后就加载 logger
    FlaskLogger(app)

    # search
    es.init_app(app)
    # websocket
    sock.init_app(app)

    app.config.from_object(config)
    regsiter_cli(app)

    return app
