from contextvars import ContextVar
from datetime import UTC, datetime
from typing import ParamSpec, TypeVar

import jwt
from flask import Flask, Response, request

from src.config import config
from src.util.exception import RequestParamsError, Unauthorization
from src.util.validation import body

from .interface import LoginScheme, User

P = ParamSpec("P")
R = TypeVar("R")

# >>> user = current_user.get()
# 可以使用 proxy 封装以便直接使用 current_user
current_user: ContextVar[User | None] = ContextVar("user")


class JWTToken:
    algorithm: str = config.ALGORITHM
    secret_key: str = config.SECRET_KEY
    access_token_expires = config.ACCESS_TOKEN_EXPIRES_DELTA

    @classmethod
    def encode_token(cls: type["JWTToken"], data: dict[str, str]) -> str:
        """Encodes the payload and returns a JWT token."""
        expire = datetime.now(UTC) + cls.access_token_expires
        data["exp"] = str(int(expire.timestamp()))

        return jwt.encode(data, cls.secret_key, cls.algorithm)

    @classmethod
    def decode_token(cls: type["JWTToken"], token: str) -> dict[str, str]:
        """Decodes the JWT token and returns the payload."""
        try:
            return jwt.decode(token, cls.secret_key, [cls.algorithm])
        except jwt.ExpiredSignatureError:
            # 过期
            raise Unauthorization(error_code=10402, message="Token expired") from None
        except jwt.InvalidTokenError:
            # 无效
            raise Unauthorization(error_code=10403, message="Invalid token") from None


class Auth:
    """Authentication and Authorization.

    Authenticates username and password and implements JWT Token-based Authorization.

    Examples:
    >>> Auth(app, User)
    >>> auth = Auth()
    >>> auth.init_app(app, User)
    """

    user: type[User]
    token_url: str = "/token"

    def __init__(self, app: Flask | None = None, user: type[User] | None = None) -> None:
        if app and user:
            self.init_app(app, user)

    def init_app(self, app: Flask, user: type[User]) -> None:
        self.app = app
        self.user = user
        app.add_url_rule(self.token_url, view_func=body(LoginScheme)(self.login), methods=["POST"])
        app.before_request(self.before_request)
        app.after_request(self.after_request)

    def before_request(self) -> None:
        user = self.identify(silent=True)
        self.current_user_token = current_user.set(user)

    def after_request(self, response: Response) -> Response:
        if hasattr(self, "current_user_token") and self.current_user_token:
            current_user.reset(self.current_user_token)
        return response

    @staticmethod
    def get_bearer_token(silent: bool = False) -> str | None:
        """Extracts the token from the authorization header."""
        authorization = request.headers.get("Authorization", "")
        if not authorization or not authorization.startswith("Bearer "):
            if silent:
                return None
            raise Unauthorization()
        return authorization[7:]

    def authenticate(self, username: str, password: str, scope: str = "") -> dict[str, str]:
        """Authenticates the user and returns an access token."""
        scopes = scope.split()  # noqa
        user = self.user.validate(username, password)
        if user is None:
            raise RequestParamsError(code=400, error_code=10401, message="Invalid credentials")
        data = {"sub": user.get_primary_value()}
        token = JWTToken.encode_token(data)
        return {"access_token": token}

    def identify(self, silent: bool = False) -> User | None:
        """Returns the current user."""
        token = self.get_bearer_token(silent)
        if token is None:
            return None
        data = JWTToken.decode_token(token)
        user = self.user.get_instance_by_primary(data["sub"])
        if user is None:
            if silent:
                return None
            raise RequestParamsError(code=400, message="Invalid user")
        return user

    def login(self, data: LoginScheme) -> dict[str, str]:
        return self.authenticate(data.username, data.password)
