from .common import PageSchema


class NoticeSchema(PageSchema):
    type: int  # 0-查询未读消息，1-查询所有消息
