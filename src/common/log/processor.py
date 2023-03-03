import logging
import re

import structlog


def combined_logformat(
    _: logging.Logger, __: str, event_dict: structlog.typing.EventDict
) -> structlog.typing.EventDict:
    """Custom processor for Gunicorn access events.

    应用在 struclog 的 processor 中, 后期会使用自定义 access
    """
    if event_dict.get("logger") == "gunicorn.access":
        message = event_dict["event"]

        parts = [
            r"(?P<host>\S+)",  # host %h
            r"\S+",  # indent %l (unused)
            r"(?P<user>\S+)",  # user %u
            r"\[(?P<time>.+)\]",  # time %t
            r'"(?P<request>.+)"',  # request "%r"
            r"(?P<status>[0-9]+)",  # status %>s
            r"(?P<size>\S+)",  # size %b (careful, can be '-')
            r'"(?P<referer>.*)"',  # referer "%{Referer}i"
            r'"(?P<agent>.*)"',  # user agent "%{User-agent}i"
        ]
        pattern = re.compile(r"\s+".join(parts) + r"\s*\Z")
        m = pattern.match(message)
        res = m.groupdict()  # type: ignore[union-attr]

        if res["user"] == "-":
            res["user"] = None

        res["status"] = int(res["status"])

        if res["size"] == "-":
            res["size"] = 0
        else:
            res["size"] = int(res["size"])

        if res["referer"] == "-":
            res["referer"] = None

        event_dict.update(res)

        del event_dict["event"]
        # del event_dict["host"]
        del event_dict["user"]
        del event_dict["time"]
        del event_dict["size"]
        del event_dict["agent"]
        del event_dict["thread"]
    return event_dict
