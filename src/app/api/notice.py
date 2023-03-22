from typing import Any

from flask import Blueprint
from sqlalchemy import update
from src.common.auth import current_user, login_required
from src.common.db import session
from src.util.exception import Forbidden, ParameterError, Updated
from src.util.validation import parameter

from app.model.notice import Notice
from app.schema.common import ResultPageSchema
from app.schema.notice import NoticeSchema

bp = Blueprint("notice", __name__, url_prefix="/notice")


@bp.get("")
@login_required
@parameter(NoticeSchema)
def get_all_message(params: NoticeSchema) -> dict[str, Any]:
    # 获取所有消息 type指定为1是获取用户所有消息, 0是获取所有未读消息
    user = current_user.get()
    notices = []
    count = 0
    if params.type == 1:
        # 获取所有历史消息
        notices = Notice.get_all(page=params.page, count=params.count, to_user_id=user.id)
        count = Notice.count(to_user_id=user.id)
    elif params.type == 0:
        # 获取未读消息
        notices = Notice.get_all(page=params.page, count=params.count, to_user_id=user.id, is_read=0)
        count = Notice.count(to_user_id=user.id, is_read=0)
    return ResultPageSchema(  # type: ignore
        page=params.page,
        count=params.count,
        total=count,
        items=list(notices),
    ).dict()


@bp.put("/<int:id>")
@login_required
def notice_is_read(id: int) -> dict[str, str]:
    user = current_user.get()
    notice = Notice.get_model_by_id(id)
    if notice is None:
        raise ParameterError(message="消息不存在")
    if notice.to_user_id != user.id:
        raise Forbidden(message="只能已读自己的消息")
    if notice.is_read:
        raise ParameterError(message="通知已读")
    notice.is_read = 1
    notice.save()
    return Updated(message="已读").to_dict()


@bp.put("")
@login_required
def notice_all_is_read() -> dict[str, str]:
    user = current_user.get()
    with session:
        session.execute(
            update(Notice)
            .where(
                Notice.to_user_id == user.id,
                Notice.is_read == 0,
            )
            .values(is_read=1)
        )
        session.commit()
    return Updated(message="已读所有").to_dict()
