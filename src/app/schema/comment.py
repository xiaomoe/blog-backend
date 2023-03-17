from pydantic import BaseModel

from .common import PageSchema


class CommentSchema(PageSchema):
    post_id: int


class ReplaySchema(PageSchema):
    comment_id: int


class CommentCreateSchema(BaseModel):
    post_id: int
    parent_id: int = 0
    root_id: int = 0
    content: str
