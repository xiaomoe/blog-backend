import logging

from gunicorn.glogging import Logger as _GunicornLogger

from src.common.log.log import Logger
from src.config import config as _config

Logger(is_production=False, log_level=_config.LOG_LEVEL)

bind = "0.0.0.0:5000"

reload = True

# Logging


class GunicornLogger(_GunicornLogger):  # type: ignore
    def __init__(self, cfg):  # type: ignore # noqa
        self.error_log = logging.getLogger("gunicorn.error")
        # self.error_log.propagate = True
        # self.error_handlers = []
        self.error_log.level = logging.INFO

        self.access_log = logging.getLogger("gunicorn.access")
        # self.access_log.propagate = True
        # self.access_handlers = []
        self.access_log.level = logging.INFO
        self.cfg = cfg

    def access(self, resp, req, environ, request_time):  # type: ignore # noqa
        """
        不使用此处记录 access 日志
        """
        pass


logger_class = GunicornLogger
