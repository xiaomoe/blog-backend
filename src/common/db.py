from contextvars import ContextVar
from typing import cast

from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from werkzeug.local import LocalProxy

from src.config import config

ctx_session: ContextVar["Session"] = ContextVar("session")


class DB:
    def __init__(self, app: Flask | None = None) -> None:

        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        self.app = app
        url: str = config.SQLALCHEMY_DATABASE_URI
        pool_size: int = config.SQLALCHEMY_POOL_SIZE
        app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)

        app.before_request(self.before_request)
        app.teardown_request(self.teardown_request)

        connect_args = {"check_same_thread": False} if "sqlite" in url else {}

        self.engine = create_engine(
            url,
            connect_args=connect_args,
            pool_size=pool_size,
            pool_recycle=7200,
        )
        self.Session = sessionmaker(self.engine)
        app.extensions["sqlalchemy"] = self

    def connect(self) -> "Session":
        """生成新的 session."""
        # session 并不代表连接 只有 exec 时才会真正连接数据库
        # session 可以看作是本地缓存
        return self.Session()

    def teardown_request(self, exception: BaseException | None) -> None:
        try:
            session = ctx_session.get()
            session.close()
            ctx_session.reset(self.token)
        except LookupError:
            pass

    def before_request(self) -> None:
        # 每次 request 创建新的 session 确保事务正确
        self.token = ctx_session.set(self.connect())


db = DB()
session = cast("Session", LocalProxy(ctx_session))
