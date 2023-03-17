from pydantic import BaseModel, Field, validator

from .common import PageSchema


class PostSchema(PageSchema):
    category_id: int | None = None
    source: int | None = None


class PostArchiveSchema(PageSchema):
    count: int = Field(10, ge=1, le=50, description="1 <= count <= 50")


class PostCreateSchema(BaseModel):
    title: str
    summary: str | None = None
    content: str
    cover: str
    category_id: int
    source: int
    # allow_comment: int
    tags: list[dict]  # ["hello"]


class PostLike(BaseModel):
    post_id: int
    type: int = 1  # 1 喜欢，0-取消喜欢

    @validator("type")
    def validate_type(cls, val):
        if val < 0 or val > 1:
            raise ValueError("只能是 0 或 1")


class TagSearchSchema(BaseModel):
    q: str


class CategorySchema(PageSchema):
    pass


class TagCreateSchema(BaseModel):
    name: str
