from collections.abc import Callable
from functools import wraps
from typing import TYPE_CHECKING, Any

from flask import Blueprint, Flask, current_app, request
from flask.wrappers import Response
from orjson import loads
from simple_websocket import ConnectionClosed
from simple_websocket import Server as _Server
from structlog import getLogger
from wsproto.events import (
    AcceptConnection,
    BytesMessage,
    CloseConnection,
    Ping,
    Pong,
    RejectConnection,
    Request,
    TextMessage,
)
from wsproto.extensions import PerMessageDeflate
from wsproto.frame_protocol import CloseReason
from wsproto.utilities import LocalProtocolError

from src.common.auth.auth import JWTToken

if TYPE_CHECKING:
    from _typeshed.wsgi import WSGIEnvironment
    from structlog.stdlib import BoundLogger

logger: "BoundLogger" = getLogger("ws")


class Server(_Server):  # type: ignore[misc]
    """在 simple_websocket 基础上增加鉴权."""

    def __init__(
        self,
        environ: "WSGIEnvironment",
        subprotocols: list[Any] | None = None,
        receive_bytes: int = 4096,
        ping_interval: int | None = None,
        max_message_size: int | None = None,
        thread_class: Any = None,
        event_class: Any = None,
        selector_class: Any = None,
    ) -> None:
        # token验证成功后保存 user_id
        self.user_id: int | None = None
        super().__init__(
            environ,
            subprotocols,
            receive_bytes,
            ping_interval,
            max_message_size,
            thread_class,
            event_class,
            selector_class,
        )

    def _handle_events(self) -> bool:  # noqa
        keep_going = True
        out_data = b""
        for event in self.ws.events():
            try:
                if isinstance(event, Request):
                    # 首次连接时鉴权
                    token = None
                    for item in event.extra_headers:
                        if item[0] == b"token":
                            # 前端传入的 token
                            token = item[1].decode("utf-8")
                    if token is None or (data := JWTToken.decode_token(token)) is None:
                        # 验证未通过 拒绝连接
                        out_data += self.ws.send(RejectConnection(status_code=401))
                    else:
                        # 验证通过 token中的数据 {'sub': user_id}
                        self.user_id = int(data["sub"])
                        self.subprotocol = self.choose_subprotocol(event)
                        out_data += self.ws.send(
                            AcceptConnection(subprotocol=self.subprotocol, extensions=[PerMessageDeflate()])
                        )
                elif isinstance(event, CloseConnection):
                    if self.is_server:
                        out_data += self.ws.send(event.response())
                    self.close_reason = event.code
                    self.close_message = event.reason
                    self.connected = False
                    self.event.set()
                    keep_going = False
                elif isinstance(event, Ping):
                    out_data += self.ws.send(event.response())
                elif isinstance(event, Pong):
                    self.pong_received = True
                elif isinstance(event, TextMessage | BytesMessage):
                    self.incoming_message_len += len(event.data)  # type: ignore
                    if self.max_message_size and self.incoming_message_len > self.max_message_size:  # type: ignore
                        out_data += self.ws.send(CloseConnection(CloseReason.MESSAGE_TOO_BIG, "Message is too big"))
                        self.event.set()
                        keep_going = False
                        break
                    if self.incoming_message is None:  # type: ignore
                        # store message as is first
                        # if it is the first of a group, the message will be
                        # converted to bytearray on arrival of the second
                        # part, since bytearrays are mutable and can be
                        # concatenated more efficiently
                        self.incoming_message = event.data
                    elif isinstance(event, TextMessage):
                        if not isinstance(self.incoming_message, bytearray):
                            # convert to bytearray and append
                            self.incoming_message = bytearray((self.incoming_message + event.data).encode())
                        else:
                            # append to bytearray
                            self.incoming_message += event.data.encode()
                    else:
                        if not isinstance(self.incoming_message, bytearray):
                            # convert to mutable bytearray and append
                            self.incoming_message = bytearray(self.incoming_message + event.data)
                        else:
                            # append to bytearray
                            self.incoming_message += event.data
                    if not event.message_finished:
                        continue
                    if isinstance(self.incoming_message, str | bytes):
                        # single part message
                        self.input_buffer.append(self.incoming_message)
                    elif isinstance(event, TextMessage):
                        # convert multi-part message back to text
                        self.input_buffer.append(self.incoming_message.decode())  # type: ignore
                    else:
                        # convert multi-part message back to bytes
                        self.input_buffer.append(bytes(self.incoming_message))  # type:ignore
                    self.incoming_message = ""
                    self.incoming_message_len = 0
                    self.event.set()
                else:
                    pass
            except LocalProtocolError:
                out_data = b""
                self.event.set()
                keep_going = False
        if out_data:
            self.sock.send(out_data)
        return keep_going


class Sock:
    def __init__(self, app: Flask | None = None) -> None:
        self.app = app
        self.bp: Blueprint = Blueprint("websocket", __name__)
        self.all_ws: set[Server] = set()
        self.after_close: Callable[[Any], Any] | None = None
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        app.register_blueprint(self.bp)

    def register_after_close(self, func: Callable[[Any], Any]) -> None:
        # 注册前端关闭连接后操作
        self.after_close = func

    @property
    def client_count(self) -> int:
        return len(self.all_ws)

    def route(self, path: str, **kwargs: Any) -> Callable[[Any], Any]:
        """Decorator to create a WebSocket route.

        The decorated function will be invoked when a WebSocket client
        establishes a connection, with a WebSocket connection object passed
        as an argument. Example::

            @sock.route('/ws')
            def websocket_route(ws):
                # The ws object has the following methods:
                # - ws.send(data)
                # - ws.receive(timeout=None)
                # - ws.close(reason=None, message=None)

        If the route has variable components, the ``ws`` argument needs to be
        included before them.

        :param path: the URL associated with the route.
        :param kwargs: additional route options. See the Flask documentation
                       for the ``app.route`` decorator for details.
        """

        def decorator(f: Callable[[Any], Any]) -> Callable[[Any], Any]:
            @wraps(f)
            def websocket_route(*args: Any, **kwargs: Any) -> Any:
                if not self.app and not self.bp:
                    raise
                ws = Server(request.environ, **current_app.config.get("SOCK_SERVER_OPTIONS", {}))
                self.all_ws.add(ws)
                try:
                    f(ws, *args, **kwargs)
                except ConnectionClosed:
                    # 删除保存的客户端
                    self.all_ws.remove(ws)
                    if self.after_close:
                        self.after_close(self)
                try:
                    ws.close()
                except Exception as e:
                    logger.exception(str(e))

                class WebSocketResponse(Response):
                    def __call__(self, *args: Any, **kwargs: Any) -> Any:
                        if ws.mode == "gunicorn":
                            raise StopIteration()
                        if ws.mode == "werkzeug":
                            raise ConnectionError()
                        return []

                return WebSocketResponse()

            kwargs["websocket"] = True
            return self.bp.route(path, **kwargs)(websocket_route)

        return decorator

    def broadcast(self, message: Any) -> None:
        # 广播
        for item in self.all_ws:
            item.send(message)

    def get_ws_by_user_id(self, id: int) -> Server | None:
        # 通过 user_id 获得 ws 实例
        for item in self.all_ws:
            if item.user_id == id:
                return item
        return None

    def send_one(self, id: int, message: Any) -> None:
        # 向某个用户发送消息
        client = self.get_ws_by_user_id(id)
        if client:
            client.send(message)


sock = Sock()


class Message:
    type: str  # noqa
    message: Any


@sock.register_after_close
def register_close(server: Sock) -> Any:
    # 关闭连接后逻辑
    for item in server.all_ws:
        # 通知所有在线用户 目前在线人数
        item.send(sock.client_count)
    return ""


@sock.route("/ws")
def echo(ws):  # type: ignore # noqa
    # 首次进入更新在线用户 并通知所有在线用户
    for item in sock.all_ws:
        item.send(sock.client_count)
    sock.all_ws.add(ws)
    while True:
        data = ws.receive()
        try:
            data = loads(data)
        except Exception as e:
            logger.exception(str(e))
        # >>> ws.send(sock.client_count)
        ws.send(ws.user_id)
