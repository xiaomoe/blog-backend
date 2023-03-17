from datetime import datetime

from sqlmodel import Field

from app.model.base import BaseSQLModel


class Comment(BaseSQLModel):
    id: int | None = Field(default=None, primary_key=True)
    post_id: int
    user_id: int
    root_id: int = Field(default=0, description="所属根评论 id，0表示本身就是根评论")
    parent_id: int = Field(default=0, description="所属父评论 id，0-表示本身就是根评论，没有父级")
    replay_count: int = Field(default=0, description="如果是 root ，需要统计它的回复数量")

    ip: str = Field(default=None, max_length=16, description="ip地址")
    platform: str = Field(default=None, max_length=16, description="客户端")
    device: str = Field(default=None, max_length=16, description="设备")
    content: str = Field(..., max_length=400, description="评论内容")

    status: int = Field(default=1, description="状态，1-正常，0-不显示，2-作者置顶，3-管理员置顶")
    create_time: datetime | None = Field(default_factory=datetime.now, description="创建时间")
    is_deleted: int = Field(default=0, nullable=False, description="是否删除,0-未删除，1-已删除")
