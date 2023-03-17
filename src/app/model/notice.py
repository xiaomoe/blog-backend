from datetime import datetime

from sqlmodel import Field

from .base import BaseSQLModel


class Notice(BaseSQLModel, table=True):

    id: int | None = Field(default=None, primary_key=True)
    content: str = Field(..., max_length=200, description="内容")
    to_user_id: int = Field(..., index=True, description="接收用户 id")
    from_user_id: int = Field(default=0, index=True, description="发送消息用户id,0-系统")
    is_read: int = Field(default=0, description="是否已读：0-未读，1-已读")
    create_time: datetime | None = Field(default_factory=datetime.now, description="创建时间")
