from flask import Flask

from .demo import demo


def regsiter_cli(app: Flask) -> None:
    app.cli.add_command(demo)
