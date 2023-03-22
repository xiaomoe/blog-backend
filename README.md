[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Moe Blog

blog backend of Moe.

> 本项目还在迭代中。

- 统一异常处理
- 参数校验
- 静态资源处理
- 权限管理 jwt RBAC
- 定时任务/任务队列
- redis 缓存系统
- websocket 通信
- 统一日志处理
- ~~代码规范(部分)~~


## TODO

- cos token 获取需要错误重试
- 第三方服务使用 celery
- logger 默认存储在当前项目的 logs 文件夹下，下一步优化为可配置项
- SQLAlchemy 与 Pydantic 结合，参考 SQLModel 的 main.py 实现 MetaClass
