import time
import uuid

import structlog
from flask import Flask, Response, g, request

access_logger: structlog.stdlib.BoundLogger = structlog.get_logger("api.access")
error_logger: structlog.stdlib.BoundLogger = structlog.get_logger("api.error")


class FlaskLogger:
    def __init__(self, app: Flask) -> None:
        self.app = app

        self.registe_log()

    def registe_log(self) -> None:
        @self.app.before_request
        def log_request_before() -> None:
            structlog.contextvars.clear_contextvars()
            request_id = str(uuid.uuid4())
            structlog.contextvars.bind_contextvars(
                request_id=request_id,
            )
            g.start_time = time.perf_counter_ns()

        @self.app.after_request
        def log_request_after(response: Response) -> Response:
            process_time = time.perf_counter_ns() - g.start_time if hasattr(g, "start_time") else -1
            http_method = request.method
            url = request.url
            http_version = request.environ.get("SERVER_PROTOCOL")
            status_code = response.status_code
            remote_addr = request.remote_addr
            access_logger.info(
                f"""{remote_addr} - "{http_method} {url} HTTP/{http_version}" {status_code}""",
                http={
                    "url": f"{request.url}",
                    "status_code": status_code,
                    "method": http_method,
                    "version": http_version,
                },
                network={"client": remote_addr},
                duration=process_time,
            )
            return response

        self.app.logger = error_logger
