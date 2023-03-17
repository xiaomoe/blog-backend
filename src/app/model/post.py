from datetime import datetime

from sqlalchemy import TEXT, Column
from sqlmodel import Field, Index, delete, select
from src.common.db import session

from .base import BaseSQLModel
from .user import User


class PostCategory(BaseSQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(..., max_length=32, unique=True, nullable=False, description="分类名称")
    info: str | None = Field(default=None, max_length=100, description="描述")
    banner: str | None = Field(default=None, max_length=255, description="背景图")
    sort: int = Field(default=1, description="排序")
    status: int = Field(default=1, nullable=False, description="状态：1可见，0-不可见")
    create_time: datetime | None = Field(default_factory=datetime.now, description="创建时间")
    update_time: datetime | None = Field(default_factory=datetime.now, description="更新时间")
    is_deleted: int = Field(default=0, nullable=False, description="是否删除，0-未删除，1-已删除")

    __tableargs__ = (Index("name_del", "name", "is_deleted", unique=True),)


class Tag(BaseSQLModel, table=True):

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(..., max_length=32, nullable=False, description="标签名称")
    color: str | None = Field(default=None, max_length=32, description="文字颜色")
    bg: str | None = Field(default=None, max_length=32, description="背景颜色")
    status: int = Field(default=1, nullable=False, description="状态(保留字段)：1可见，0-不可见")


class Post(BaseSQLModel, table=True):

    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(..., max_length=128, nullable=False, description="文章标题")
    summary: str = Field(..., max_length=200, description="简介")
    content: str = Field(..., sa_column=(Column("content", TEXT)), description="文章内容")
    cover: str | None = Field(default=None, max_length=255, description="头图 url")
    category_id: int = Field(default=0, description="所属分类 id， 0 表示没有分类")
    # tags: str | None = Field(default=None, max_length=255, description="标签 ids")
    source: int = Field(default=1, description="来源，1-原创，2-转载，3-翻译")
    publish: int = Field(default=1, description="可见范围：1-公开，2-登录，3-仅自己")
    status: int = Field(
        default=1,
        nullable=False,
        description="状态：1可见，0-不可见,2-作者置顶，3-管理员置顶",
    )
    sort: int = Field(default=1, description="排序")
    allow_comment: int = Field(default=1, description="是否允许评论, 1-允许，0-不允许")

    create_time: datetime | None = Field(default_factory=datetime.now, description="创建时间")
    update_time: datetime | None = Field(default_factory=datetime.now, description="更新时间")
    is_deleted: int = Field(default=0, nullable=False, description="是否删除,0-未删除，1-已删除")

    user_id: int = Field(..., description="作者 id")
    view_count: int = Field(default=0, description="文章浏览量")
    like_count: int = Field(default=0, description="点赞量")
    comment_count: int = Field(default=0, description="评论数")

    __tableargs__ = (Index("name", "name"), Index("status", "status"))

    def update_post(self) -> dict:
        item = self.dict(exclude={"user_id", "category_id", "tags", "is_deleted"})
        user = User.get_model_by_id(self.user_id)
        item["user"] = user
        category = PostCategory.get_model_by_id(self.category_id)
        item["category"] = category
        # tags = []
        # if self.tags is not None and self.tags != "":
        #     tags = session.exec(select(PostTag).where(PostTag.id.in_(self.tags.split(",")))).all()  # type:ignore
        # item["tags"] = tags
        return item

    @property
    def tags(self):
        res = []
        with session:
            _tags = session.exec(select(PostTag.tag_id).where(PostTag.post_id == self.id)).all()
            for tag_id in _tags:
                tag = Tag.get_model_by_id(tag_id)
                res.append(tag)

        return res

    @tags.setter
    def tags(self, data: list[dict]):

        with session:
            if self.id is None:
                session.refresh(self)
            new_tags = set()
            old_tags = set()
            for item in data:
                _tag = Tag.get_model_by_attr(name=item["name"])
                if _tag is None:
                    _tag = Tag(name=item["name"])
                    session.add(_tag)
                    session.refresh(_tag)
                new_tags.add(_tag.id)
            _tags = session.exec(select(PostTag).where(PostTag.post_id == self.id)).all()
            for item in _tags:
                old_tags.add(item.tag_id)
            in_tags = new_tags - old_tags
            out_tags = old_tags - new_tags
            for item in in_tags:
                post_tag = PostTag(post_id=self.id, tag_id=item)  # type: ignore
                session.add(post_tag)
            for item in out_tags:
                session.execute(delete(PostTag).where(PostTag.post_id == self.id, PostTag.tag_id == item))
            session.commit()

    @property
    def category(self):
        cate = {"id": 0, "name": "默认分类"}
        if self.category_id > 0:
            res = PostCategory.get_model_by_id(self.category_id)
            if res:
                cate = res.dict(include={"id", "name"})
        return cate

    @property
    def user(self):
        user = User.get_model_by_id(self.user_id)
        if user is None:
            return {}
        return {
            "id": user.id,
            "username": user.username,
            "avatar": user.avatar,
        }


class PostTag(BaseSQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    post_id: int = Field(..., description="文章 id")
    tag_id: int = Field(..., description="tag id")


class PostAttitude(BaseSQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    post_id: int = Field(..., description="文章 id")
    user_id: int = Field(..., description="用户 id")
    attitude: int = Field(..., description="态度：1-喜欢，0-不喜欢")
    create_time: datetime | None = Field(default_factory=datetime.now, description="创建时间")
    update_time: datetime | None = Field(default_factory=datetime.now, description="更新时间")


class File(BaseSQLModel, table=True):

    id: int | None = Field(default=None, primary_key=True)
    md5: str = Field(..., description="唯一标识")
    user_id: int = Field(..., description="用户 id")
    location: int = Field(default=1, description="文件保存位置：1-本地，2-云")
    type: int = Field(default=0, description="文件类型：0-未知，1-图片，2-视频，3-音频")
    ext: str | None = Field(default=None, description="后缀")
    path: str = Field(..., max_length=100, description="路径或 url")
    name: str = Field(..., description="名称")
    create_time: datetime | None = Field(default_factory=datetime.now, description="创建时间")
    update_time: datetime | None = Field(default_factory=datetime.now, description="更新时间")

    __tableargs__ = (Index("user_file", "user_id", "md5"),)
