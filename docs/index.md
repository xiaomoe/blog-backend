# Moe Blog

## 1. 项目结构

TODO

## 2. 开发规范

### 2.1 代码风格和规范

- 使用 ruff 进行代码静态检测，并使用 black 格式化，使用 mypy 做类型检测。
- 文件及目录使用单数名称、使用 _ 连接字符。
- 内容使用utf8编码格式。
- API 文档自动生成：使用工具如 Swagger 自动生成 API 文档，方便其他开发者快速了解 API 接口的用法和参数说明。
- 文档和注释：在应用设计和实现时需要编写清晰明了的文档和注释，方便其他开发者和维护人员了解应用的功能和实现细节，提升应用的可维护性和可读性。

### 2.2 API 规范

- URL：单词使用`-`连接。
- Method：GET（查询），POST（创建），PUT（修改），DELETE（删除）。
- JSON 格式

Flask 2.2+ 在内部实现了返回 dict 和 list 时的自动 json 化，但对于更多类型没有支持，需要黑魔法支持一下——在解析返回值（app.make_response）之前，全部将返回数据变成 dict 或者 list。

- dict、list
- str、int、byte
- HTTPException
- Pydantic BaseModel

```python
# 1. 拦截函数处理 make_response，在真正处理 rv之前将返回的data转换成 JSON Response。
# 2. 替换app.json.proverder.dumps ，处理那些不支持的数据类型，比如 pydantic 的 BaseModel。也可以直接将内置json替换成为 orjson。
# 3. 处理其它，在json中没有处理的类型，比如Exception，因为 Flask 提供了错误处理装饰器，所以还是按照其逻辑处理
# 3.1 app.errorhandler(HTTPException) 使其data返回 dict 类型
# 3.2 自定义错误，app.errorhandler(APIException)，也将 data 返回 dict 类型
class OrJSONProvider(JSONProvider):
    def dumps(self, obj: t.Any, **kwargs: t.Any) -> str:
        try:
            res = orjson.dumps(obj)
        except Exception:
            # deal with other type
            if isinstance(obj, ToDictLike):
                res = orjson.dumps(obj.dict())
            if isinstance(obj, ToAsDictLike):
                res = orjson.dumps(obj.as_dict())
            raise
        return res.decode()

    def loads(self, s: str | bytes, **kwargs: t.Any) -> t.Any:
        return orjson.loads(s)

class APIFlask(Flask):
    json_provider_class = OrJSONProvider

    def make_response(self, rv: ResponseReturnValue) -> Response:
        """change to json Response"""
        if isinstance(rv, tuple):
            data, *other = rv
            rv = self.json.response(data), *other  # type: ignore
        elif not isinstance(rv, Response):
            rv = self.json.response(rv)

        return super().make_response(rv)
```

#### 2.2.1 HTTP 响应码

- 200 Success
- 201 Created
- 204 No Content 
- 301 Moved Permanently
- 302 Found 临时更改
- 304 Not Modified 缓存响应
- 400 Bad Request 客户端错误
- 401 Unauthorized 无授权
- 403 Forbidden 无权限
- 404 Not Found 资源不存在
- 405 Method Not Allowed 方法不允许
- 422 Unprocessable Entity 请求参数校验失败
- 429 Too Many Requests 请求过多
- 500 Internal Server Error 服务端未知错误
- 502 Bad Gateway   代理正常，后端有错误
- 503 Service Unavailable  服务暂不可用
- 504 Gateway Timeout   代理正常，但连接不到后端

#### 2.2.2 响应数据

```python
# 自定义异常
class APIException(Exception):
    code: int = 500
    error_code: int = 10000
    message: str = "内部错误"

    def __init__(self, code: int | None = None, error_code: int | None = None, message: str | None = None) -> None:
        if code is not None:
            self.code = code
        if error_code is not None:
            self.error_code = error_code
        if message is not None:
            self.message = message
        super().__init__()

    def dict(self) -> dict[str, t.Any]:
        return {
            "code": self.code,
            "error_code": self.error_code,
            "message": self.message,
        }
# 之后将其注册到errorhandler，通过 error.dict()将data转换成dict即可。
```

异常响应

```json
{
    "code": "404",
    "error_code": "10001",
    "message": "资源不存在"
}
```

正常响应，直接返回数据（dict or list）

```json
{
    "data": []
}
```

### 2.3 环境变量规范

- 来源：代码中特别指定，当前 SHELL变量，.env 文件，默认值。
- 优先级：依次递减。
- 面向：生产、开发。

#### 2.3.1 .env 文件

- 文件区分生产、开发（.env.production, .env）
- 变量名大写(`FLASK_`, `CELERY_`, `MYSQL_`, `REDIS_`)
- 增加 APP 前缀
- 使用_连接单词

#### 2.3.2 使用变量

- Flask App 使用 app.config 使用相关变量或直接使用 `config.config`实例。
- Python 相关 APP 使用 pydantic 封装的 Config 类调用。
- 非 Python 相关如 MySQL、Redis，通过 docker 直接读取 .env 文件。

#### 2.3.3 生产部署

将 .env.production 替换成 .env 并将 secret 存储到 SHELL 或者其它地方，防止提交到仓库。

## 3. 异常处理规范

错误处理：定义常见错误码和错误信息，使得应用在出现错误时能够快速响应并给出明确的错误提示信息。

- Flask 内部错误（HTTPException），通过 errorhandler形式转换成dict，从而可以 json 化。
- 手动触发 自定义错误（APIException），类似手段，自动化处理成 JSON 格式。
- 调用第三方产生错误。TODO

## 4. 参数校验规范

对输入的参数进行验证和过滤，防止SQL注入和XSS攻击。

结合 pydantic 实现 request query和json数据的校验。

## 5. 静态资源处理

对于应用中的静态资源，如图片、CSS、JS 等，需要使用 CDN 进行加速和缓存，提升应用的加载速度和用户体验。

采用第三方服务腾讯 COS。

## 6. 日志记录

日志记录：对于关键操作和错误情况，应该记录相关日志信息，方便排查问题和追踪应用运行情况。对应用中的日志进行管理和分析，使用工具如 ELK Stack、Splunk 等，方便定位问题和调试，提升应用的可维护性和可靠性。

## 7. 权限管理

- 认证（Authentication）：登录并颁发凭证（credentials），比如 token 或 session。登录方式有多种，比如用户名密码。
- 鉴权（Authorization）：验证传入的凭证是否合格，是否具有操作权限（Who can do What in Which Object），比如RBAC。
- OAuth2 是一种规范（specification），定义了处理身份认证（Authentication）和授权（Authorization）的几种方式。
- OpenAPI 构建 API 的开放规范。它在 security scheme （安全方案）中集成了 OAuth2 规范。Security Scheme 中定义了许多安全性的 type，用于规范安全认证和验证过程。
  - apikey：在header、query 或 cookie 中传递 api 密钥。比如在 url中加入`?apikey=xxx`。
  - http：标准的 HTTP 认证系统，包括 baisc、bearer、digest等方案。常用的是 一个带有值为 `Bearer` 的 `Authorization` 头部加上一个令牌，它也是从 OAuth2 继承而来的。
  - **oauth2（flows）**：目前流行的处理认证和授权的方案标准。
    - authorizationCode flow：基于 oauth2 的第三方认证。
    - clientCredentials flow: 基于 oauth2 的第三方认证。
    - **password flow**：最简单的认证，可以直接在同一个应用中使用。

  - openIdConnect：自动获取OAuth2 认证数据，属于 OpenID Connect 规范（基于 OAuth2 并扩展了的规范）。
  - mutualTLS 等


```yaml
type: oauth2
description: Optional for security scheme
flows:
  password:
    tokenUrl: https://example.com/api/oauth/token
    refreshUrl: https://example.com/api/oauth/refresh-token
    scopes:
      write:pets: modify pets in your account
      read:pets: read your pets
  authorizationCode:
    authorizationUrl: https://example.com/api/oauth/dialog
    tokenUrl: https://example.com/api/oauth/token
    scopes:
      write:pets: modify pets in your account
      read:pets: read your pets 
```

或

```yaml
type: apiKey
description: Optional for security scheme
in: query
name: apikey
```

或者（与 OAuth2 的 password 使用一致的 JWT）将 token 添加 `Bearer ` 后添加到 header 的 Authorization 中。

```yaml
type: http
scheme: bearer
bearerFormat: JWT
```

或者（每次请求都使用用户名和密码，base64编码添加 `Basic ` 前缀后添加到 header 的 Authorization 中）。

```yaml
type: http
scheme: basic
```

现在可以理解为有两个总体步骤：authentication 和 authorization。OAuth2 中定义的是授权过程，但大多针对的第三方登录，对于同一应用来讲可以把 OAuth2 的 password 流作为 authentication 和 authorization 部分，即使用 username 和 password 的 json 数据（标准是使用 form）进行认证，之后使用 bearer 进行 authorization（鉴权/授权）。

### 认证

用户名和密码进行登录，认证成功返回 access_token。

还要注意凭证安全问题：

|  auth   |   Storage    |                    Security                    |
| :-----: | :----------: | :--------------------------------------------: |
| session |    Cookie    | CSRF（Cross-site request forgery）跨站请求伪造 |
|  token  | localStorage |    XSS (Cross-Site Scripting) 跨站脚本攻击     |

### 鉴权

使用基于 RBAC 的权限管理系统。

Access Control List

| 权限\角色 | 管理员 | 撰稿者 | 普通用户 |
| :-------: | :----: | :----: | :------: |
| 查看文章  |   ✓    |   ✓    |    ✓     |
| 发布文章  |   ✓    |   ✓    |          |
| 编辑文章  |   ✓    |   ✓    |          |
| 删除文章  |   ✓    |   ✓    |          |
| 点赞文章  |   ✓    |   ✓    |    ✓     |
| 评论文章  |   ✓    |   ✓    |    ✓     |

TODO 前端菜单和按钮权限资源？是否可以合并

| resource_id | name     | type    | parent_id |
| ----------- | -------- | ------- | --------- |
| 1           | 用户管理 | menu    | NULL      |
| 2           | 角色管理 | menu    | NULL      |
| 3           | 权限管理 | menu    | NULL      |
| 4           | 日志管理 | menu    | NULL      |
| 5           | 用户列表 | submenu | 1         |
| 6           | 新增用户 | button  | 1         |
| 7           | 编辑用户 | button  | 1         |
| 8           | 删除用户 | button  | 1         |
| 9           | 角色列表 | submenu | 2         |
| 10          | 新增角色 | button  | 2         |
| 11          | 编辑角色 | button  | 2         |
| 12          | 删除角色 | button  | 2         |
| 13          | 权限列表 | submenu | 3         |
| 14          | 新增权限 | button  | 3         |
| 15          | 编辑权限 | button  | 3         |
| 16          | 删除权限 | button  | 3         |
| 17          | 登录日志 | submenu | 4         |
| 18          | 操作日志 | submenu | 4         |

[CSRF Protection in Flask | TestDriven.io --- Flask 中的 CSRF 保护 |测试驱动.io](https://testdriven.io/blog/csrf-flask/)

[2-12 微服务项目的鉴权.html](file:///C:/Users/diaoh/Downloads/2-12 微服务项目的鉴权.html)

[Web Authentication Methods Compared | TestDriven.io --- Web 身份验证方法比较 |测试驱动.io](https://testdriven.io/blog/web-authentication-methods/)

[Introduce OAuth 2.0 — Authlib 1.2.0 documentation --- 引入 OAuth 2.0 — Authlib 1.2.0 文档](https://docs.authlib.org/en/latest/oauth/2/intro.html#intro-oauth2)

[Security Intro - FastAPI --- 安全介绍 - FastAPI (tiangolo.com)](https://fastapi.tiangolo.com/tutorial/security/)

[Intro to IAM - Learn about Identity Access Management - Auth0 --- IAM 简介 - 了解身份访问管理 - Auth0](https://auth0.com/intro-to-iam)

[Security Intro - FastAPI (tiangolo.com)](https://fastapi.tiangolo.com/tutorial/security/)

## 8. 缓存设计

- 缓存对象：一个路由函数、一个对象、用户状态等。
- 缓存位置：本地缓存、redis缓存。
- 缓存内容：string、dict、zset等。

![image-20230307134322035](C:\Users\diaoh\OneDrive\assets\img\4-开发管理\image-20230307134322035.png)

前端缓存（不涉及）、nginx静态资源缓存（不涉及）、路由缓存、数据库缓存（不涉及）。

所以主要实现了基于路由或对后端数据库查询的缓存。存储在redis 或直接内存中。

### 缓存模式

#### 读写缓存一致性

同时操作的有写操作就会产生不一致现象：读写、写写。读读则不会产生不一致，但会导致缓存穿透。

目前方案：这种方案只有读写才会不一致，写写都是删除。

- 先更新 storage （DB）
- 再删除 cache

这个问题会导致缓存穿透，改进为：不直接删除，而是设置30s的过期时间。

#### 多级缓存一致性

- 先清理下游缓存
- 下游缓存 expire 要大于上游（×2倍）

#### 热点缓存

多 cluster

### 过期策略

要指定过期实践，并设置淘汰策略（LRU）。

- 缓存雪崩：随机过期时间、服务熔断、请求限流、redis 高可用集群。
- 缓存击穿：热点key永不过期。
- 缓存穿透：布隆过滤器、缓存空值（3-5分钟）、请求入口检测。

### 缓存预热

启动项目时加载缓存数据。

### 常用场景

UV（按照 IP统计）使用HyperLogLog 统计，总数统计，自动去重，但存在一定偏差。

用户是否在线，使用 bitmap ，两值判断，即使很多人也不会使用很大空间。0-1

判断某值是否存在（大数据量下），使用布隆过滤器（需要按照 module）

list：热点列表、队列

string：递增

hash：用户资料（登录名作为key）、购物车（id作为key）

set：标签系统（文章分类、共同好友）交集、黑名单（in）。

sorted set：排行榜、权重排序

优秀项目：https://github.com/Yiling-J/cacheme/

![ ](C:\Users\diaoh\OneDrive\assets\img\4-开发管理\image-20230312192533031.png)

## 9. 部署方案

TODO
