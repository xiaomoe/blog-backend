from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from src.app.model.base import BaseModel, T_create_time, T_id


class Comment(BaseModel):
    id: Mapped[T_id] = mapped_column(init=False)
    post_id: Mapped[int]
    user_id: Mapped[int]
    content: Mapped[str] = mapped_column(String(400), comment="评论内容")
    root_id: Mapped[int] = mapped_column(default=0, comment="所属根评论 id, 0表示本身就是根评论")
    parent_id: Mapped[int] = mapped_column(default=0, comment="所属父评论 id, 0-表示本身就是根评论, 没有父级")
    replay_count: Mapped[int] = mapped_column(default=0, comment="如果是 root, 需要统计它的回复数量")

    ip: Mapped[str] = mapped_column(String(16), default=None, comment="ip 地址")
    platform: Mapped[str] = mapped_column(String(20), default="", comment="客户端")
    device: Mapped[str] = mapped_column(String(20), default="", comment="设备")

    status: Mapped[int] = mapped_column(default=1, comment="状态: 1-正常, 0-不显示, 2-作者置顶, 3-管理员置顶")
    create_time: Mapped[T_create_time] = mapped_column(default=None, comment="创建时间")
    is_deleted: Mapped[int] = mapped_column(default=0, comment="是否删除,0-未删除, 1-已删除")


class CommentLike(BaseModel):
    id: Mapped[T_id] = mapped_column(init=False)
    user_id: Mapped[int] = mapped_column()
    comment_id: Mapped[int] = mapped_column()
    create_time: Mapped[T_create_time] = mapped_column(default=None, comment="创建时间")
