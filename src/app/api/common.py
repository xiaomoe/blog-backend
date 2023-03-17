import random
from datetime import timedelta

from flask import Blueprint
from src.common.auth import login_required
from src.common.redis import redis
from src.util.exception import ParameterError, Success
from task import send_sms

from app.schema.user import CodeSchema

bp = Blueprint("common", __name__)


@bp.route("/code", methods=["GET"])
@login_required
def get_code(params: CodeSchema):
    code = generate_digit_code()
    key = f"{params.type}:{params.mobile}"
    if redis.get(key):
        raise ParameterError(message="请稍后重试")
    send_sms.delay(params.mobile, code, timedelta(minutes=5))
    redis.set(key, code, ex=timedelta(minutes=5))  # TODO: send_sms 和 redis set 原子性？消息队列？
    return Success(message="发送验证码成功")


def generate_digit_code(size: int = 4) -> str:
    """生成数字类型随机验证码.

    Args:
        size (int, optional): 字符个数. Defaults to 4.

    Returns:
        str: 验证码
    """
    words = "1234567890"
    return "".join(random.choices(words, k=size))
