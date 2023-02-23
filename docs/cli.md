## Flask 自定义指令

Flask 内部提供 click 支持的指令，内置指令有

- flask run
- flask --app app run --reload

通过内置的 flask.cli 模块可以设置自定义指令，比如初始化数据库、提供虚拟数据等。

## 如何自定义指令

与指令有关的方法都在 flask.cli 模块下。

常用形式是在一组命令（AppGroup）下创建子命令，并指定子命令的选项或参数。最后通过app.cli.add_command()进行注册。在app.cli注册的命令都Application Context

```python
import click
from flask.cli import AppGroup


db_cli = AppGroup('db')

@db_cli.command('init')
@click.argument('name')
def init(name):
    pass

app.cli.add_command(db_cli)
```

之后便可以在 shell 中使用
```bash
# 初始化
flask db init admin
# 创建 admin 和 group
flask db create admin
```

## 参考

https://flask.palletsprojects.com/en/2.2.x/cli/
