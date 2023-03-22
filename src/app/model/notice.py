from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from src.app.model.base import BaseModel, T_create_time, T_id


class Notice(BaseModel):
    id: Mapped[T_id] = mapped_column(init=False)
    content: Mapped[str] = mapped_column(String(200), comment="内容")
    to_user_id: Mapped[int] = mapped_column(index=True, comment="接收用户 id")
    from_user_id: Mapped[int] = mapped_column(default=0, index=True, comment="发送消息用户id,0-系统")
    is_read: Mapped[int] = mapped_column(default=0, comment="是否已读: 0-未读, 1-已读")
    create_time: Mapped[T_create_time] = mapped_column(default=None, comment="创建时间")
