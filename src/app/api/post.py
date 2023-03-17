from flask import Blueprint, g
from sqlmodel import and_, col, delete, func, or_, select
from src.common.auth import login_required, permission_meta
from src.common.db import session
from src.util.exception import Created, Deleted, Forbidden, ParameterError, Success, Unautorization, Updated
from src.util.validation import body, parameter

from app.model.post import Post, PostAttitude, PostCategory, PostTag, Tag
from app.model.user import User
from app.schema.admin import CategoryCreateSchema
from app.schema.common import ResultPageSchema
from app.schema.post import (
    CategorySchema,
    PostArchiveSchema,
    PostCreateSchema,
    PostLike,
    PostSchema,
    TagCreateSchema,
    TagSearchSchema,
)

bp = Blueprint("post", __name__, url_prefix="/post")


@bp.route("", methods=["GET"])
@login_required(optional=True)
@parameter(PostSchema)
def get_posts(params: PostSchema):
    """分页获取文章列表"""
    current_user = None
    if hasattr(g, "user_id"):
        user = User.get_model_by_id(g.user_id)
        if user is not None:
            current_user = user

    statement = select(Post).order_by(-col(Post.create_time))
    if params.category_id:
        statement = statement.where(Post.category_id == params.category_id)
    if current_user is None:
        statement = statement.where(Post.publish < 2)
    else:
        statement = statement.where(
            or_(col(Post.publish) < 3, and_(col(Post.publish) == 3, col(Post.user_id) == current_user.id))
        )

    statement = statement.offset(params.count * params.page).limit(params.count)
    with session:
        result = session.exec(statement).all()
        res = []
        for item in result:
            data = item.dict(
                exclude={
                    "content",
                    "category_id",
                    "allow_comment",
                    "user_id",
                    "is_deleted",
                }
            )
            data["tags"] = item.tags
            data["category"] = item.category
            data["user"] = item.user
            res.append(data)
        return ResultPageSchema(
            page=params.page,
            count=params.count,
            total=0,  # TODO 获得对应范围的文章数量
            items=res,
        ).dict()


@bp.route("/<int:id>", methods=["GET"])
@login_required(optional=True)
def get_post(id):
    """获取文章详情"""
    user = current_user()
    post = Post.get_model_by_id(id)
    if post is None:
        raise ParameterError(message="文章不存在")
    if post.publish == 2 and user is None:
        raise Unautorization(message="请登录后查看")
    if post.publish == 3 and (user is None or user.id != post.user_id):
        raise Forbidden(message="无权查看此文章")

    res = post.dict(
        exclude={
            "is_deleted",
            "category_id",
            "sort",
            "status",
            "user_id",
        }
    )
    res.update(
        {
            "tags": post.tags,
            "category": post.category,
            "user": post.user,
        }
    )
    return res


@bp.route("/archive", methods=["GET"])
@login_required(optional=True)
@parameter(PostArchiveSchema)
def get_post_archive(params: PostArchiveSchema):
    """获得归档文章"""
    user = current_user()
    statement = select(Post)
    if user is None:
        statement = statement.where(Post.publish < 2)
    else:
        statement = statement.where(
            or_(col(Post.publish) < 3, and_(col(Post.publish) == 3, col(Post.user_id) == user.id))
        )
    statement.offset(params.count * params.page).limit(params.count)
    with session:
        result = session.exec(statement).all()
        res = []
        for item in result:
            res.append(item.dict(include={"id", "title", "summary", "create_time"}))
        return res


@bp.route("", methods=["POST"])
@permission_meta(auth="创建文章", module="post")
@body(PostCreateSchema)
def create_post(body: PostCreateSchema):
    """创建文章"""
    existed = Post.get_model_by_attr(title=body.title)
    if existed:
        raise ParameterError(message="标题已经存在")
    if body.category_id > 0:
        # 0 表示默认分类（未分类）
        category = PostCategory.get_model_by_id(body.category_id)
        if category is None:
            raise ParameterError(message="分类不存在")
    user = current_user()
    if user is None:
        raise Forbidden(message="不能修改别人的文章")
    if body.summary is None:
        body.summary = body.content[:200]
    post = Post.parse_obj(body.dict(exclude_defaults=True))
    post.user_id = user.id  # type: ignore
    post = post.save()
    for tag in body.tags:
        tag_obj = Tag.get_model_by_id(tag["id"])  # type: ignore
        if tag_obj is None:
            raise ParameterError(message="标签不正确")
        PostTag(post_id=post.id, tag_id=tag["id"]).save()  # type:ignore
    return Created(message="创建文章成功")


@bp.route("/<int:id>", methods=["PUT"])
@permission_meta(auth="更新文章", module="post")
@body(PostCreateSchema)
def update_post(body: PostCreateSchema, id):
    post = Post.get_model_by_id(id)
    if post is None:
        raise ParameterError(message="文章不存在")
    user = current_user()
    if user is None or user.id != post.user_id:
        raise Forbidden(message="不能修改别人的文章")
    category = PostCategory.get_model_by_id(body.category_id)
    if category is None:
        raise ParameterError(message="分类不存在")
    post.update(body)
    return Updated(message="修改文章成功")


def current_user() -> User | None:
    _user = None
    if hasattr(g, "user_id"):
        user = User.get_model_by_id(g.user_id)
        if user is not None:
            _user = user
    return _user


@bp.post("/category")
@permission_meta(auth="创建分类", module="post")
@body(CategoryCreateSchema)
def create_category(body: CategoryCreateSchema):
    """创建分类"""
    data = body.dict(exclude_unset=True)
    existed = PostCategory.get_model_by_attr(name=body.name)
    if existed:
        raise ParameterError(message="分类名称已经存在，请更换")
    category = PostCategory.parse_obj(data)
    category.save()
    return Created(message="创建分类成功")


@bp.put("/category/<int:id>")
@permission_meta(auth="修改分类", module="post")
@body(CategoryCreateSchema)
def update_category(body: CategoryCreateSchema, id: int):
    """修改分类"""
    cate = PostCategory.get_model_by_id(id)
    if not cate:
        raise ParameterError(message="分类不存在")
    existed = PostCategory.get_model_by_attr(name=body.name)
    if existed and existed.id != id:
        raise ParameterError(message="分类名称已经存在，请更换")
    cate.update(body)
    cate.save()
    return Updated(message="修改分类成功")


@bp.delete("/category/<int:id>")
@permission_meta(auth="删除分类", module="post")
def delete_category(id: int):
    """删除分类"""
    cate = PostCategory.get_model_by_id(id)
    if not cate:
        raise ParameterError(message="分类不存在")
    with session:
        session.delete(cate)
        session.commit()
    return Deleted(message="删除分类成功")


@bp.route("/<int:id>", methods=["DELETE"])
@permission_meta(auth="删除文章", module="post")
def delete_post(id):
    post = Post.get_model_by_id(id)
    if post is None:
        raise ParameterError(message="文章不存在")
    user = current_user()
    if user is None or user.id != post.user_id:
        raise Forbidden(message="不能修改别人的文章")
    with session:
        session.execute(delete(PostTag).where(PostTag.post_id == id))
    return Deleted(message="文章删除成功")


@bp.route("/like", methods=["POST"])
@permission_meta(auth="点赞文章", module="post")
@body(PostLike)
def post_like(body: PostLike):
    post = Post.get_model_by_id(body.post_id)
    if post is None:
        raise ParameterError(message="文章不存在")
    user = current_user()
    if user is None:
        raise Unautorization(message="请登录")
    attitude = PostAttitude.get_model_by_attr(post_id=body.post_id, user_id=user.id, attitude=1)

    if body.type == 1:
        # 点赞
        if attitude is not None:
            raise ParameterError(message="已经点赞成功，请勿重复操作")
        attitude = PostAttitude(post_id=body.post_id, user_id=user.id, attitude=1)  # type: ignore
        post.like_count += 1
        with session:
            session.add(attitude)
    elif body.type == 0:
        # 取消点赞
        attitude = PostAttitude.get_model_by_attr(post_id=body.post_id, user_id=user.id, attitude=1)
        if attitude is None:
            raise ParameterError(message="已经取消点赞成功，请勿重复操作")
        post.like_count -= 1
        with session:
            session.delete(attitude)
            session.commit()
    return Success(message="点赞成功")


@bp.route("/my", methods=["GET"])
@login_required
@parameter(PostSchema)
def my_post(params: PostSchema):
    user = current_user()
    if user is None:
        raise ParameterError(message="用户不存在")
    with session:
        posts = session.exec(
            select(Post).where(Post.user_id == user.id).offset(params.page * params.count).limit(params.count)
        ).all()
        return posts


@bp.route("/my/like", methods=["GET"])
@login_required
def my_like_posts():

    user = current_user()
    if user is None:
        raise ParameterError(message="用户不存在")
    with session:
        post_like = session.exec(
            select(PostAttitude.post_id).where(PostAttitude.user_id == user.id, PostAttitude.attitude == 1)
        )
        posts = session.exec(select(Post).where(col(Post.id).in_(post_like)))
        return posts


@bp.route("/hot", methods=["GET"])
@login_required(optional=True)
def hot_posts():
    user = current_user()
    statement = select(Post)
    if user is None:
        statement = statement.where(Post.publish < 2)
    else:
        statement = statement.where(
            or_(col(Post.publish) < 3, and_(col(Post.publish) == 3, col(Post.user_id) == user.id))
        )
    statement.order_by(func.sum(Post.like_count, Post.comment_count)).offset(0).limit(10)  # 前10条文章
    with session:
        result = session.exec(statement).all()
        return result


@bp.route("/category", methods=["GET"])
@parameter(CategorySchema)
def get_category(params: CategorySchema):
    """获取所有分类(分页)"""
    res = PostCategory.get_all(page=params.page, count=params.count)

    return ResultPageSchema(page=params.page, count=params.count, total=PostCategory.count(), items=res).dict()


@bp.get("/category/all")
def get_category_all():
    """获取所有分类(不分页)"""
    with session:
        res = session.exec(select(PostCategory.id, PostCategory.name)).all()  # type: ignore

    return {
        "items": res,
        "total": PostCategory.count(),
    }


@bp.route("/tag/search", methods=["GET"])
@parameter(TagSearchSchema)
def search_tag(params: TagSearchSchema):
    """实时搜索，返回10条"""
    with session:
        return session.exec(
            select(Tag.id, Tag.name).where(col(Tag.name).like(f"%{params.q}%")).limit(10)  # type: ignore
        ).all()  # type:ignore


@bp.post("/tag")
@body(TagCreateSchema)
def create_tag(body: TagCreateSchema):
    tag = Tag.get_model_by_attr(name=body.name)
    if tag is None:
        tag = Tag(name=body.name).save()
    return tag.dict(include={"id", "name"})
