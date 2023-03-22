from flask import Blueprint
from flask.typing import ResponseValue
from sqlalchemy import and_, delete, func, or_, select
from src.common.auth import current_user, login_required, permission_meta
from src.common.db import session
from src.util.exception import Created, Deleted, Forbidden, ParameterError, Success, Unautorization, Updated
from src.util.validation import body, parameter

from app.model.post import Category, Post, PostLike, PostTag, Tag
from app.schema.admin import CategoryCreateSchema
from app.schema.common import ResultPageSchema
from app.schema.post import (
    CategorySchema,
    PostArchiveSchema,
    PostCreateSchema,
    PostLikeSchema,
    PostSchema,
    TagCreateSchema,
    TagSearchSchema,
)

bp = Blueprint("post", __name__, url_prefix="/post")


@bp.get("")
@login_required(optional=True)
@parameter(PostSchema)
def get_posts(params: PostSchema) -> ResponseValue:
    """分页获取文章列表."""
    user = current_user.get()

    statement = select(Post).order_by(-Post.create_time)
    if params.category_id:
        statement = statement.where(Post.category_id == params.category_id)
    if current_user is None:
        statement = statement.where(Post.publish < 2)
    else:
        statement = statement.where(or_(Post.publish < 3, and_(Post.publish == 3, Post.user_id == user.id)))

    statement = statement.offset(params.count * params.page).limit(params.count)
    with session:
        result = session.scalars(statement).all()
        res = []
        for item in result:
            data = item.to_dict()
            data["tags"] = item.tags
            data["category"] = item.category
            data["user"] = item.user
            res.append(data)
        return ResultPageSchema(  # type:ignore
            page=params.page,
            count=params.count,
            total=0,  # TODO 获得对应范围的文章数量
            items=res,
        ).dict()


@bp.get("/<int:id>")
@login_required(optional=True)
def get_post(id: int) -> ResponseValue:
    """获取文章详情."""
    user = current_user.get()
    post = Post.get_model_by_id(id)
    if post is None:
        raise ParameterError(message="文章不存在")
    if post.publish == 2 and user is None:
        raise Unautorization(message="请登录后查看")
    if post.publish == 3 and (user is None or user.id != post.user_id):
        raise Forbidden(message="无权查看此文章")

    res = post.to_dict()
    res.update(
        {
            "tags": post.tags,
            "category": post.category,
            "user": post.user,
        }
    )
    return res


@bp.get("/archive")
@login_required(optional=True)
@parameter(PostArchiveSchema)
def get_post_archive(params: PostArchiveSchema) -> ResponseValue:
    """获得归档文章."""
    user = current_user.get()
    statement = select(Post)
    if user is None:
        statement = statement.where(Post.publish < 2)
    else:
        statement = statement.where(or_((Post.publish) < 3, and_((Post.publish) == 3, (Post.user_id) == user.id)))
    statement.offset(params.count * params.page).limit(params.count)
    with session:
        result = session.scalars(statement).all()
        res = []
        for item in result:
            res.append(item.to_dict())
        return res


@bp.post("")
@permission_meta(auth="创建文章", module="post")
@body(PostCreateSchema)
def create_post(body: PostCreateSchema) -> ResponseValue:
    """创建文章."""
    existed = Post.get_model_by_attr(title=body.title)
    if existed:
        raise ParameterError(message="标题已经存在")
    if body.category_id > 0:
        # 0 表示默认分类
        category = Category.get_model_by_id(body.category_id)
        if category is None:
            raise ParameterError(message="分类不存在")
    user = current_user.get()
    if user is None:
        raise Forbidden(message="不能修改别人的文章")
    if body.summary is None:
        body.summary = body.content[:200]
    post = Post(user_id=user.id, **body.dict(exclude_defaults=True))
    post = post.save()
    for tag in body.tags:

        tag_obj = Tag.get_model_by_id(tag["id"])
        if tag_obj is None:
            raise ParameterError(message="标签不正确")
        PostTag(post_id=post.id, tag_id=tag["id"]).save()
    return Created(message="创建文章成功").to_dict()


@bp.put("/<int:id>")
@permission_meta(auth="更新文章", module="post")
@body(PostCreateSchema)
def update_post(body: PostCreateSchema, id: int) -> ResponseValue:
    post = Post.get_model_by_id(id)
    if post is None:
        raise ParameterError(message="文章不存在")
    user = current_user.get()
    if user is None or user.id != post.user_id:
        raise Forbidden(message="不能修改别人的文章")
    category = Category.get_model_by_id(body.category_id)
    if category is None:
        raise ParameterError(message="分类不存在")
    post.update(body.dict())
    return Updated(message="修改文章成功").to_dict()


@bp.post("/category")
@permission_meta(auth="创建分类", module="post")
@body(CategoryCreateSchema)
def create_category(body: CategoryCreateSchema) -> ResponseValue:
    """创建分类."""
    data = body.dict(exclude_unset=True)
    existed = Category.get_model_by_attr(name=body.name)
    if existed:
        raise ParameterError(message="分类名称已经存在, 请更换")
    category = Category(**data)
    category.save()
    return Created(message="创建分类成功").to_dict()


@bp.put("/category/<int:id>")
@permission_meta(auth="修改分类", module="post")
@body(CategoryCreateSchema)
def update_category(body: CategoryCreateSchema, id: int) -> ResponseValue:
    """修改分类."""
    cate = Category.get_model_by_id(id)
    if not cate:
        raise ParameterError(message="分类不存在")
    existed = Category.get_model_by_attr(name=body.name)
    if existed and existed.id != id:
        raise ParameterError(message="分类名称已经存在，请更换")
    cate.update(body.dict())
    cate.save()
    return Updated(message="修改分类成功").to_dict()


@bp.delete("/category/<int:id>")
@permission_meta(auth="删除分类", module="post")
def delete_category(id: int) -> ResponseValue:
    """删除分类."""
    cate = Category.get_model_by_id(id)
    if not cate:
        raise ParameterError(message="分类不存在")
    with session:
        session.delete(cate)
        session.commit()
    return Deleted(message="删除分类成功").to_dict()


@bp.delete("/<int:id>")
@permission_meta(auth="删除文章", module="post")
def delete_post(id: int) -> ResponseValue:
    post = Post.get_model_by_id(id)
    if post is None:
        raise ParameterError(message="文章不存在")
    user = current_user.get()
    if user is None or user.id != post.user_id:
        raise Forbidden(message="不能修改别人的文章")
    with session:
        session.execute(delete(PostTag).where(PostTag.post_id == id))
    return Deleted(message="文章删除成功").to_dict()


@bp.post("/like")
@permission_meta(auth="点赞文章", module="post")
@body(PostLikeSchema)
def post_like(body: PostLikeSchema) -> ResponseValue:
    post = Post.get_model_by_id(body.post_id)
    if post is None:
        raise ParameterError(message="文章不存在")
    user = current_user.get()
    if user is None:
        raise Unautorization(message="请登录")
    attitude = PostLike.get_model_by_attr(post_id=body.post_id, user_id=user.id, attitude=1)

    if body.type == 1:
        # 点赞
        if attitude is not None:
            raise ParameterError(message="已经点赞成功，请勿重复操作")
        attitude = PostLike(post_id=body.post_id, user_id=user.id, attitude=1)  # type: ignore
        post.like_count += 1
        with session:
            session.add(attitude)
    elif body.type == 0:
        # 取消点赞
        attitude = PostLike.get_model_by_attr(post_id=body.post_id, user_id=user.id, attitude=1)
        if attitude is None:
            raise ParameterError(message="已经取消点赞成功，请勿重复操作")
        post.like_count -= 1
        with session:
            session.delete(attitude)
            session.commit()
    return Success(message="点赞成功").to_dict()


@bp.get("/my")
@login_required
@parameter(PostSchema)
def my_post(params: PostSchema) -> ResponseValue:
    user = current_user.get()
    with session:
        posts = session.scalars(
            select(Post).where(Post.user_id == user.id).offset(params.page * params.count).limit(params.count)
        ).all()
        return list(posts)


@bp.get("/my/like")
@login_required
def my_like_posts() -> ResponseValue:

    user = current_user.get()
    if user is None:
        raise ParameterError(message="用户不存在")
    with session:
        posts = session.scalars(
            select(Post).join(PostLike, Post.id == PostLike.post_id).where(PostLike.user_id == user.id)
        ).all()
        return list(posts)


@bp.get("/hot")
@login_required(optional=True)
def hot_posts() -> ResponseValue:
    user = current_user.get()
    statement = select(Post)
    if user is None:
        statement = statement.where(Post.publish < 2)
    else:
        statement = statement.where(or_((Post.publish) < 3, and_((Post.publish) == 3, (Post.user_id) == user.id)))
    statement.order_by(func.sum(Post.like_count, Post.comment_count)).offset(0).limit(10)  # 前10条文章
    with session:
        result = session.scalars(statement).all()
        return list(result)


@bp.get("/category")
@parameter(CategorySchema)
def get_category(params: CategorySchema) -> ResponseValue:
    """获取所有分类(分页)."""
    res = list(Category.get_all(page=params.page, count=params.count))

    return ResultPageSchema(page=params.page, count=params.count, total=Category.count(), items=res).dict()


@bp.get("/category/all")
def get_category_all() -> ResponseValue:
    """获取所有分类(不分页)."""
    with session:
        res = session.scalars(select(Category.id, Category.name)).all()

    return {
        "items": res,
        "total": Category.count(),
    }


@bp.get("/tag/search")
@parameter(TagSearchSchema)
def search_tag(params: TagSearchSchema) -> ResponseValue:
    """实时搜索, 返回10条."""
    with session:
        res = session.scalars(select(Tag.id, Tag.name).where((Tag.name).like(f"%{params.q}%")).limit(10)).all()
        return list(res)


@bp.post("/tag")
@body(TagCreateSchema)
def create_tag(body: TagCreateSchema) -> ResponseValue:
    tag = Tag.get_model_by_attr(name=body.name)
    if tag is None:
        tag = Tag(name=body.name).save()
    return tag.to_dict()
