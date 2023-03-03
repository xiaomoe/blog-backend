"""基于 structlog 的日志收集一揽子方案

该模块旨在提供一个基于 Structlog 的日志包装器来产生更好的日志记录体验,
它可以将 web 请求期间捕获的所有信息整合到单个日志记录中。
模块中的 Logger 类具有两种模式:
- 开发模式: Log 输出到 stdout。
- 生产模式: Log 输出到 文件(可以 JSON格式), 在生成环境中使用。
"""
import logging

import structlog

from .handler import LinRotatingFileHandler

# 无论开发还是生产, 标准 logging 还是 structlog 都需要的 Processors
stdlib_and_struct_processors: list[structlog.typing.Processor] = [
    # 添加上下文变量到 event_dict 最好放在第一位
    structlog.contextvars.merge_contextvars,
    structlog.stdlib.add_logger_name,
    structlog.stdlib.add_log_level,
    # 支持原生 %-style 不加也没报错 具体用在什么情形还没研究
    structlog.stdlib.PositionalArgumentsFormatter(),
    # 将 event_dict 转换成 extra 字典并再添加到 event_dict 中
    structlog.stdlib.ExtraAdder(),
    structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
    structlog.processors.StackInfoRenderer(),
    structlog.processors.UnicodeDecoder(),
]


class Logger:
    """该类是一个基于 Structlog 日志全局初始化封装, 用于将全局信息集中到单个日志中。

    全局日志设置应在入口处初始化该类。

    Attributes:
        log_level (str): 日志级别。默认值: "INFO"
        is_production (bool): 是否为生产环境。默认值: False。
        processors (list[structlog.typing.Processor]): 无论是开发还是生产环境,
            标准 logging 还是 structlog 都需要的 Processors。
        renderer (structlog.typing.Processor): event_dict to str|bytes|tuple 的处理器(processors链上暂居最后位置)。

    Examples:
        >>> import structlog
        >>> import logging

        >>> Logger(is_production=True, log_level="INFO")

        >>> logger = structlog.get_logger()
        >>> logger.info("Message from structlog.")
        >>> logging.info("Message from logging.")
    """

    log_level = "INFO"
    is_production = False
    # event_dict -> event_dict
    processors: list[structlog.typing.Processor]
    # event_dict -> str | bytes | tuple
    # Processors 链最后一个
    renderer: structlog.typing.Processor

    def __init__(self, log_level: str = "INFO", is_production: bool = True) -> None:
        self.log_level = log_level
        self.is_production = is_production
        self.processors = stdlib_and_struct_processors
        if is_production:
            # 将 异常堆栈 格式化
            self.processors.append(structlog.processors.format_exc_info)

            self.renderer = structlog.dev.ConsoleRenderer(colors=False)
            # 还可以使用 json
            # self.renderer = structlog.processors.JSONRenderer(serializer=json.dumps)
        else:
            self.renderer = structlog.dev.ConsoleRenderer(colors=True)

        self.init_structlog()
        self.init_stdliblog()

    def init_structlog(self) -> None:
        """设置全局 structlog 配置"""
        structlog.configure(
            processors=[
                *self.processors,
                # 因为需要使用 ProcessorFormatter, 所以最后一个必须是这个
                # ProcessorFormatter 内部的 chain 最后一个必须是 renderer
                structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )

    def init_stdliblog(self) -> None:
        """设置标准库 root logger"""
        formatter = structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=self.processors,
            processors=[
                # 去除 event_dict 中的 _record 和 _from
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                self.renderer,
            ],
        )
        root = logging.getLogger()
        if self.is_production:
            file_handler = LinRotatingFileHandler()
            file_handler.setFormatter(formatter)
            root.addHandler(file_handler)
        else:
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            root.addHandler(handler)

        root.setLevel(self.log_level)

    def clear_thrid(self, *logger_names: str) -> None:
        """清除第三方库中名为 logger_names 的 handler 并设置向上传递交给 root logger 处理.

        Args:
            logger_names: 要清除和传递的logger名称列表.
        """
        for logger_name in logger_names:
            logger = logging.getLogger(logger_name)
            logger.handlers.clear()
            logger.propagate = True

    def clear_gunicorn(self) -> None:
        """清除gunicorn 中 access 和 error 的 handlers.

        由于 gunicorn.glogging 中设置逻辑 实际此处代码无效 需要子类化覆盖
        """
        self.clear_thrid("gunicorn.access", "gunicorn.error")
