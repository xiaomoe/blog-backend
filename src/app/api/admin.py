from flask import Blueprint
from flask.typing import ResponseValue
from sqlalchemy import delete, func, select, update
from src.common.auth import admin_required, current_user
from src.common.auth.auth import JWTToken
from src.common.db import session
from src.util.exception import Created, Deleted, ParameterError, Success, Updated
from src.util.validation import body, parameter

from app.model.comment import Comment
from app.model.post import Category, Post, PostTag, Tag
from app.model.user import Permission, Role, RolePermission, User
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


@bp.post("/login")
@body(AdminLoginSchema)
def admin_login(body: AdminLoginSchema) -> ResponseValue:
    """管理员登陆."""
    user = User.get_model_by_attr(mobile=body.mobile)
    if user is None:
        raise ParameterError(message="请检查用户名和密码")

    token = JWTToken.encode_token({"sub": str(user.id)})
    return {"token": token}


@bp.get("/profile")
@admin_required
def admin_profile() -> ResponseValue:
    """管理员信息获取."""
    user = current_user.get()
    return user.to_dict()


@bp.route("/user", methods=["GET"])
@admin_required
@parameter(UserSchema)
def get_all_user(params: UserSchema) -> ResponseValue:
    statement = select(User).offset(params.page * params.count).limit(params.count)
    count = User.count()
    with session:
        result = session.scalars(statement).all()
        return {"page": params.page, "count": params.count, "total": count, "items": result}


@bp.delete("/user/<int:id>")
@admin_required
def delete_user(id: int) -> ResponseValue:
    with session:
        session.execute(delete(User).where(User.id == id))
        session.commit()
    return Deleted(message="删除用户成功").to_dict()


@bp.put("/user/<int:id>")
@admin_required
@body(UserUpdateSchema)
def update_user(body: UserUpdateSchema, id: int) -> ResponseValue:
    """修改角色."""
    with session:
        user = User.get_model_by_id(id)
        if user:
            user.role_id = body.group_id
        session.commit()

    return Updated(message="更新用户分组成功").to_dict()


@bp.get("/role")
@admin_required
def get_roles() -> ResponseValue:
    with session:
        roles = session.scalars(select(Role)).all()
    return list(roles)


@bp.get("/role/<int:id>")
@admin_required
def get_role_and_permission(id: int) -> ResponseValue:
    role = Role.get_model_by_id(id)
    if role is None:
        raise ParameterError(message="分组不存在")
    with session:
        permissions = session.scalars(
            select(Permission)
            .join(RolePermission, Permission.id == RolePermission.permission_id)
            .where(RolePermission.role_id == id)
        ).all()
    return {
        "id": role.id,
        "name": role.name,
        "info": role.info,
        "permissions": permissions,
    }


@bp.post("/role")
@admin_required
@body(GroupCreateSchema)
def create_role(body: GroupCreateSchema) -> ResponseValue:
    existed = Role.get_model_by_attr(name=body.name)
    if existed is not None:
        raise ParameterError(message="分组名称已存在，请更换")
    role = Role(name=body.name, info=body.info).save()
    if body.permission_ids is not None:
        with session:
            permissions = session.scalars(select(Permission.id).where(Permission.id.in_(body.permission_ids))).all()
            for permission in permissions:
                RolePermission(role_id=role.id, permission_id=permission.id)
            session.commit()

    return Created(message="创建分组成功").to_dict()


@bp.put("/role/<int:id>")
@admin_required
@body(GroupUpdateSchema)
def update_role(body: GroupUpdateSchema, id: int) -> ResponseValue:
    existed = Role.get_model_by_attr(name=body.name)
    if existed is not None:
        raise ParameterError(message="分组名称已存在 请更换")
    role = Role.get_model_by_id(id)
    if role is None:
        raise ParameterError(message="要修改的分组不存在")
    role.name = body.name
    role.info = body.info
    role.save()
    return Updated(message="更新分组成功").to_dict()


@bp.route("/role/<int:id>", methods=["DELETE"])
@admin_required
def delete_role(id: int) -> ResponseValue:
    """删除角色."""
    existed = Role.get_model_by_id(id)
    if existed is None:
        raise ParameterError(message="分组不存在")
    with session:
        session.delete(existed)
    return Deleted(message="删除分组成功").to_dict()


@bp.get("/can_dispatch_permission")
@admin_required
def get_can_dispatch_permission() -> ResponseValue:
    """获得所有可分配权限."""
    return ""


@bp.route("/permission", methods=["GET"])
@admin_required
def get_permissions() -> ResponseValue:
    """获得所有权限."""
    with session:
        permissions = session.scalars(select(Permission)).all()
    return list(permissions)


@bp.route("/permission/dispatch", methods=["POST"])
@admin_required
@body(PermissionDispatch)
def dispatch_permission(body: PermissionDispatch) -> ResponseValue:
    """给分组分配单个权限."""
    role_existed = Role.get_model_by_id(body.group_id)
    if role_existed is None:
        raise ParameterError(message="分组不存在")
    permission_existed = Permission.get_model_by_id(body.permission_id)
    if permission_existed is None:
        raise ParameterError(message="权限不存在")
    role_permission = RolePermission(role_id=role_existed.id, permission_id=permission_existed.id)
    role_permission.save()
    return Updated(message="分组权限更新成功").to_dict()


@bp.route("/permission/dispatch/batch", methods=["POST"])
@admin_required
@body(PermissionDispatchBatch)
def dispatch_batch_permission(body: PermissionDispatchBatch) -> ResponseValue:
    """给分组分配一组权限."""
    group_existed = Role.get_model_by_id(body.group_id)
    if group_existed is None:
        raise ParameterError(message="分组不存在")
    with session:
        permission_ids = session.scalars(select(Permission.id).where(Permission.id._in(body.permission_ids))).all()
        for permission_id in permission_ids:
            group_permission = RolePermission(role_id=group_existed.id, permission_id=permission_id)
            session.add(group_permission)
        session.commit()

    return Updated(message="分组权限更新成功").to_dict()


@bp.route("/post")
@admin_required
@parameter(PostSchema)
def get_posts(params: PostSchema) -> ResponseValue:
    statement = select(Post)
    if params.category_id is not None:
        statement = statement.where(Post.category_id == params.category_id)
    if params.start_date is not None and params.end_date is not None:  # 有start_date 则必须有 end_date
        if params.start_date > params.end_date:
            raise ParameterError(message="结束时间必须大于等于起始时间")
        statement = statement.where(Post.create_time.between(params.start_date, params.end_date))
    statement.offset(params.count * params.page).limit(params.count)
    with session:
        result = session.scalars(statement).all()
        return list(result)


@bp.route("/post/<int:id>", methods=["GET"])
@admin_required
def get_post_detail(id: int) -> ResponseValue:
    """文章详情."""
    post = Post.get_model_by_id(id)
    if post is None:
        raise ParameterError(message="文章不存在")
    return post.to_dict()


@bp.route("/post/<int:id>/status", methods=["PUT"])
@admin_required
@body(PostStatusSchema)
def change_post_status(body: PostStatusSchema, id: int) -> ResponseValue:
    """修改文章状态，置顶还是隐藏."""
    post = Post.get_model_by_id(id)
    if post is None:
        raise ParameterError(message="文章不存在")
    if body.status == post.status:
        raise ParameterError(message="文章已经是当前状态了 请不要重复操作")
    post.status = body.status
    post.save()
    return Updated(message="修改文章状态成功").to_dict()


@bp.route("/category", methods=["GET"])
@admin_required
def get_category() -> ResponseValue:
    """获得所有分类(不分页)."""
    with session:
        res = session.scalars(select(Category)).all()
        return list(res)


@bp.route("/category", methods=["POST"])
@admin_required
@body(CategoryCreateSchema)
def create_category(body: CategoryCreateSchema) -> ResponseValue:
    """创建分类."""
    data = body.dict(exclude_unset=True)
    existed = Category.get_model_by_attr(name=body.name)
    if existed:
        raise ParameterError(message="分类名称已经存在 请更换")
    category = Category(**data)
    category.save()
    return Created(message="创建分类成功").to_dict()


@bp.route("/category/<int:id>", methods=["PUT"])
@admin_required
@body(CategoryCreateSchema)
def update_category(body: CategoryCreateSchema, id: int) -> ResponseValue:
    """修改分类."""
    cate = Category.get_model_by_id(id)
    if cate is None:
        raise ParameterError(message="分类不存在")
    cate.update(body.dict())
    cate.save()
    return Success(message="修改分类成功").to_dict()


@bp.route("/category/<int:id>", methods=["PUT"])
@admin_required
def delete_category(id: int) -> ResponseValue:
    """删除分类."""
    cate = Category.get_model_by_id(id)
    if cate is None:
        raise ParameterError(message="分类不存在")
    # 删除分类 则该分类下所有文章的 分类 id 设为 0
    with session:
        session.execute(update(Post).where(Post.category_id == id).values({"category_id": 0}))
        session.delete(cate)
        session.commit()
    return Deleted(message="删除成功").to_dict()


@bp.route("/tag", methods=["GET"])
@admin_required
@parameter(TagSchema)
def tags(params: TagSchema) -> ResponseValue:
    """获得所有标签(不分页)."""
    tags = Tag.get_all(params.page, params.count)
    return list(tags)


@bp.route("/tag", methods=["POST"])
@admin_required
@body(TagCreateSchema)
def create_tag(body: TagCreateSchema) -> ResponseValue:
    """创建标签."""
    data = body.dict(exclude_unset=True)
    existed = Tag.get_model_by_attr(name=body.name)
    if existed:
        raise ParameterError(message="标签已经存在")
    tag = Tag(**data)
    tag.save()
    return Created(message="创建标签成功").to_dict()


@bp.route("/tag/<int:id>", methods=["PUT"])
@admin_required
@body(TagCreateSchema)
def update_tag(body: TagCreateSchema, id: int) -> ResponseValue:
    """更新标签 意义不大."""
    tag = Tag.get_model_by_id(id)
    if tag is None:
        raise ParameterError(message="标签不存在")
    tag.update(body.dict())
    tag.save()
    return Updated(message="修改标签成功").to_dict()


@bp.route("/tag/<int:id>", methods=["DELETE"])
@admin_required
def delete_tag(id: int) -> ResponseValue:
    """删除标签."""
    tag = Tag.get_model_by_id(id)
    if tag is None:
        raise ParameterError(message="标签不存在")
    with session:
        session.execute(delete(PostTag).where(PostTag.tag_id == id))
        session.delete(tag)
        session.commit()
    return Deleted(message="删除标签成功").to_dict()


@bp.put("/comment/<int:id>")
@admin_required
@body(CommentUpdateSchema)
def update_comment(body: CommentUpdateSchema, id: int) -> ResponseValue:
    """更新评论 主要时是置顶和拉黑."""
    comment = Comment.get_model_by_id(id)
    if comment is None:
        raise ParameterError(message="评论不存在")
    if body.type == 1:
        # 置顶
        if body.value == 0:
            comment.status = 1  # 取消置顶 恢复正常
        else:
            comment.status = 3  # 置顶
    elif body.type == 2:
        # 拉黑
        if body.value == 0:
            comment.status = 1  # 取消拉黑 恢复正常
        else:
            comment.status = 0  # 拉黑
    else:
        raise ParameterError(message="操作不允许")
    comment.save()
    return Updated(message="修改评论成功").to_dict()


@bp.delete("/comment/<int:id>")
@admin_required
def comment_delete(id: int) -> ResponseValue:
    """删除评论."""
    comment = Comment.get_model_by_id(id)
    if comment is None:
        raise ParameterError(message="评论不存在")
    with session:
        session.delete(comment)
        session.commit()
    return Deleted(message="删除分类成功").to_dict()
