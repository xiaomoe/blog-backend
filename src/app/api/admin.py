from flask import Blueprint
from sqlmodel import col, delete, func, select, update
from src.common.auth import admin_required, current_user
from src.common.auth.auth import JWTToken
from src.common.db import session
from src.util.exception import Created, Deleted, ParameterError, Success, Updated
from src.util.validation import body, parameter

from app.model.comment import Comment
from app.model.post import Post, PostCategory, PostTag, Tag
from app.model.user import Group, GroupPermission, GroupUser, Permission, User
from app.schema.admin import (
    AdminLoginSchema,
    CategoryCreateSchema,
    CommentUpdateSchema,
    GroupCreateSchema,
    GroupUpdateSchema,
    PermissionDispatch,
    PermissionDispatchBatch,
    PostSchema,
    PostStatusSchema,
    TagCreateSchema,
    TagSchema,
    UserSchema,
    UserUpdateSchema,
)

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/login", methods=["POST"])
@body(AdminLoginSchema)
def admin_login(body: AdminLoginSchema):
    """管理员登陆."""
    user = User.get_model_by_attr(mobile=body.mobile)
    if user is None:
        raise ParameterError(message="请检查用户名和密码")

    token = JWTToken.encode_token({"sub": user.id})
    return {"token": token}


@bp.get("/profile")
@admin_required
def admin_profile():
    """管理员信息获取."""
    user = current_user.get()
    return user


@bp.route("/user", methods=["GET"])
@admin_required
@parameter(UserSchema)
def get_all_user(params: UserSchema):
    statement = (
        select(User)
        .join(GroupUser, User.id == GroupUser.user_id)
        .offset(params.page * params.count)
        .limit(params.count)
    )
    all_count_statement = select(func.count(User.id)).join(GroupUser, User.id == GroupUser.user_id)  # type: ignore
    if params.group_id:
        statement = statement.where(GroupUser.group_id == params.group_id)
        all_count_statement = all_count_statement.where(GroupUser.group_id == params.group_id)
    with session:
        all_count = session.execute(all_count_statement).scalar()
        result = session.exec(statement).all()
        return {"page": params.page, "count": params.count, "total": all_count, "items": result}


@bp.delete("/user/<int:id>")
@admin_required
def delete_user(id):
    with session:
        session.execute(delete(User).where(User.id == id))
        session.execute(delete(GroupUser).where(GroupUser.user_id == id))
        session.commit()
    return Deleted(message="删除用户成功")


@bp.put("/user/<int:id>")
@admin_required
@body(UserUpdateSchema)
def update_user(body: UserUpdateSchema, id):
    user = User.get_model_by_id(id)
    if user is None:
        return ParameterError(message="用户不存在")
    with session:
        groups = session.exec(select(GroupUser.group_id).where(GroupUser.user_id == id)).all()
        if body.group_id is None:
            for group in groups:
                session.delete(group)
        else:
            new_groups = set(body.group_id) - set(groups)
            old_groups = set(groups) - set(body.group_id)
            for group_id in old_groups:
                session.execute(delete(GroupUser).where(GroupUser.group_id == group_id, GroupUser.user_id == user.id))
            for group_id in new_groups:
                session.add(GroupUser(group_id=group_id, user_id=user.id))  # type: ignore
        session.commit()

    return Updated(message="更新用户分组成功")


@bp.get("/group")
@admin_required
def get_groups():
    with session:
        groups = session.exec(select(Group)).all()
    return groups


@bp.get("/group/<int:id>")
@admin_required
def get_group_and_permission(id):
    group = Group.get_model_by_id(id)
    if group is None:
        raise ParameterError(message="分组不存在")
    with session:
        permissions = session.exec(
            select(Permission)
            .join(GroupPermission, Permission.id == GroupPermission.permission_id)
            .where(GroupPermission.group_id == id)
        ).all()
    return {
        "id": group.id,
        "name": group.name,
        "info": group.info,
        "permissions": permissions,
    }


@bp.post("/group")
@admin_required
@body(GroupCreateSchema)
def create_group(body: GroupCreateSchema):
    existed = Group.get_model_by_attr(name=body.name)
    if existed is not None:
        raise ParameterError(message="分组名称已存在，请更换")
    group = Group(name=body.name, info=body.info).save()
    if body.permission_ids is not None:
        with session:
            permissions = session.exec(
                select(Permission.id).where(  # type: ignore
                    Permission.id.in_(body.permission_ids)  # type: ignore
                )
            ).all()
            for permission in permissions:
                GroupPermission(group_id=group.id, permission_id=permission.id)  # type: ignore
            session.commit()

    return Created(message="创建分组成功")


@bp.put("/group/<int:id>")
@admin_required
@body(GroupUpdateSchema)
def update_group(body: GroupUpdateSchema, id):
    existed = Group.get_model_by_attr(name=body.name)
    if existed is not None:
        raise ParameterError(message="分组名称已存在，请更换")
    group = Group.get_model_by_id(id)
    if group is None:
        raise ParameterError(message="要修改的分组不存在")
    group.name = body.name
    group.info = body.info
    group.save()
    return Updated(message="更新分组成功")


@bp.route("/group/<int:id>", methods=["DELETE"])
@admin_required
def delete_group(id):
    """删除分组"""
    existed = Group.get_model_by_id(id)
    if existed is None:
        raise ParameterError(message="分组不存在")
    with session:
        session.delete(existed)
    return Deleted(message="删除分组成功")


@bp.get("/can_dispatch_permission")
@admin_required
def get_can_dispatch_permission():
    """获得所有可分配权限"""
    return ""


@bp.route("/permission", methods=["GET"])
@admin_required
def get_permissions():
    """获得所有权限"""
    with session:
        permissions = session.exec(select(Permission)).all()
    return permissions


@bp.route("/permission/dispatch", methods=["POST"])
@admin_required
@body(PermissionDispatch)
def dispatch_permission(body: PermissionDispatch):
    """给分组分配单个权限"""
    group_existed = Group.get_model_by_id(body.group_id)
    if group_existed is None:
        raise ParameterError(message="分组不存在")
    permission_existed = Permission.get_model_by_id(body.permission_id)
    if permission_existed is None:
        raise ParameterError(message="权限不存在")
    group_permission = GroupPermission(group_id=group_existed.id, permission_id=permission_existed.id)  # type: ignore
    group_permission.save()
    return Updated(message="分组权限更新成功")


@bp.route("/permission/dispatch/batch", methods=["POST"])
@admin_required
@body(PermissionDispatchBatch)
def dispatch_batch_permission(body: PermissionDispatchBatch):
    """给分组分配单个权限"""
    group_existed = Group.get_model_by_id(body.group_id)
    if group_existed is None:
        raise ParameterError(message="分组不存在")
    with session:
        permission_ids = session.exec(
            select(Permission.id).where(  # type: ignore
                Permission.id._in(body.permission_ids)  # type: ignore
            )
        ).all()
        for permission_id in permission_ids:
            group_permission = GroupPermission(group_id=group_existed.id, permission_id=permission_id)  # type: ignore
            session.add(group_permission)
        session.commit()

    return Updated(message="分组权限更新成功")


@bp.route("/post")
@admin_required
@parameter(PostSchema)
def get_posts(params: PostSchema):
    statement = select(Post)
    if params.category_id is not None:
        statement = statement.where(Post.category_id == params.category_id)
    if params.start_date is not None and params.end_date is not None:  # 有start_date 则必须有 end_date
        if params.start_date > params.end_date:
            raise ParameterError(message="结束时间必须大于等于起始时间")
        statement = statement.where(col(Post.create_time).between(params.start_date, params.end_date))
    statement.offset(params.count * params.page).limit(params.count)
    with session:
        result = session.exec(statement).all()
        posts = []
        for item in result:
            post = item.update_post()
            posts.append(post)
        return posts


@bp.route("/post/<int:id>", methods=["GET"])
@admin_required
def get_post_detail(id):
    """文章详情"""
    post = Post.get_model_by_id(id)
    if post is None:
        raise ParameterError(message="文章不存在")
    return post.update_post()


@bp.route("/post/<int:id>/status", methods=["PUT"])
@admin_required
@body(PostStatusSchema)
def change_post_status(body: PostStatusSchema, id):
    """修改文章状态，置顶还是隐藏"""
    post = Post.get_model_by_id(id)
    if post is None:
        raise ParameterError(message="文章不存在")
    if body.status == post.status:
        raise ParameterError(message="文章已经是当前状态了，请不要重复操作")
    post.status = body.status
    post.save()
    return Updated(message="修改文章状态成功")


@bp.route("/category", methods=["GET"])
@admin_required
def get_category():
    """获得所有分类（不分页）"""
    with session:
        return session.exec(select(PostCategory)).all()


@bp.route("/category", methods=["POST"])
@admin_required
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


@bp.route("/category/<int:id>", methods=["PUT"])
@admin_required
@body(CategoryCreateSchema)
def update_category(body: CategoryCreateSchema, id):
    """修改分类"""
    cate = PostCategory.get_model_by_id(id)
    if cate is None:
        raise ParameterError(message="分类不存在")
    cate.update(body)
    cate.save()
    return Success(message="修改分类成功")


@bp.route("/category/<int:id>", methods=["PUT"])
@admin_required
def delete_category(id):
    """删除分类"""
    cate = PostCategory.get_model_by_id(id)
    if cate is None:
        raise ParameterError(message="分类不存在")
    # 删除分类，则该分类下所有文章的 分类 id 设为 0
    with session:
        session.execute(update(Post).where(Post.category_id == id).values({"category_id": 0}))
        session.delete(cate)
        session.commit()
    return Deleted(message="删除成功")


@bp.route("/tag", methods=["GET"])
@admin_required
@parameter(TagSchema)
def tags(params: TagSchema):
    """获得所有标签（不分页）"""
    tags = Tag.get_all(params.page, params.count)
    return tags


@bp.route("/tag", methods=["POST"])
@admin_required
@body(TagCreateSchema)
def create_tag(body: TagCreateSchema):
    """创建标签"""
    data = body.dict(exclude_unset=True)
    existed = Tag.get_model_by_attr(name=body.name)
    if existed:
        raise ParameterError(message="标签已经存在")
    tag = Tag.parse_obj(data)
    tag.save()
    return Created(message="创建标签成功")


@bp.route("/tag/<int:id>", methods=["PUT"])
@admin_required
@body(TagCreateSchema)
def update_tag(body: TagCreateSchema, id):
    """更新标签，意义不大"""
    tag = Tag.get_model_by_id(id)
    if tag is None:
        raise ParameterError(message="标签不存在")
    tag.update(body)
    tag.save()
    return Updated(message="修改标签成功")


@bp.route("/tag/<int:id>", methods=["DELETE"])
@admin_required
def delete_tag(id):
    """删除标签"""
    tag = Tag.get_model_by_id(id)
    if tag is None:
        raise ParameterError(message="标签不存在")
    with session:
        session.execute(delete(PostTag).where(PostTag.tag_id == id))
        session.delete(tag)
        session.commit()
    return Deleted(message="删除标签成功")


@bp.put("/comment/<int:id>")
@admin_required
@body(CommentUpdateSchema)
def update_comment(body: CommentUpdateSchema, id):
    """更新评论，主要时是置顶和拉黑"""
    comment = Comment.get_model_by_id(id)
    if comment is None:
        raise ParameterError(message="评论不存在")
    if body.type == 1:
        # 置顶
        if body.value == 0:
            comment.status = 1  # 取消置顶，恢复正常
        else:
            comment.status = 3  # 置顶
    elif body.type == 2:
        # 拉黑
        if body.value == 0:
            comment.status = 1  # 取消拉黑，恢复正常
        else:
            comment.status = 0  # 拉黑
    else:
        raise ParameterError(message="操作不允许")
    comment.save()
    return Updated(message="修改评论成功")


@bp.delete("/comment/<int:id>")
@admin_required
def comment_delete(id):
    """删除评论"""
    comment = Comment.get_model_by_id(id)
    if comment is None:
        raise ParameterError(message="评论不存在")
    with session:
        session.delete(comment)
        session.commit()
    return Deleted(message="删除分类成功")
