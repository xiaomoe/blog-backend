from click import echo
from flask.cli import AppGroup

demo = AppGroup("demo")


@demo.command("say")
def test_demo() -> None:
    echo("hello cli")
