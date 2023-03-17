from flask import Blueprint
from sqlmodel import select
from src.common.auth import current_user, permission_meta
from src.common.db import session
from src.util.exception import Created, ParameterError
from src.util.validation import body, parameter

from app.model.comment import Comment
from app.model.post import Post
from app.schema.comment import CommentCreateSchema, CommentSchema, ReplaySchema

bp = Blueprint("comment", __name__, url_prefix="/comment")


@bp.route("", methods=["GET"])
@parameter(CommentSchema)
def get_comments(params: CommentSchema):
    with session:
        comments = session.exec(
            select(Comment)
            .where(Comment.post_id == params.post_id, Comment.root_id == 0)
            .offset(params.page * params.count)
            .limit(params.count)
        ).all()

        res = {
            "page": params.page,
            "count": params.count,
            "total": Comment.count(),
            "items": [],
        }
        for comment in comments:
            replay = session.exec(select(Comment).where(Comment.root_id == comment.id).limit(3)).all()
            item = comment.dict()
            item["replay"] = replay
            res["items"].append(item)
    return res


@bp.route("/replay", methods=["GET"])
@parameter(ReplaySchema)
def get_replay(params: ReplaySchema):
    comment = Comment.get_model_by_id(params.comment_id)
    if comment is None:
        raise ParameterError(message="评论不存在")
    with session:
        replay = session.exec(
            select(Comment)
            .where(Comment.root_id == params.comment_id)
            .offset(params.page * params.count)
            .limit(params.count)
        ).all()
    return {"page": params.page, "count": params.count, "total": comment.replay_count, "items": replay}


@bp.route("", methods=["POST"])
@permission_meta(auth="发表评论", module="comment")
@body(CommentCreateSchema)
def create_comment(body: CommentCreateSchema):
    # 从 request 中获得 ip、客户端、设备信息
    user = current_user.get()
    post = Post.get_model_by_id(body.post_id)
    if post is None:
        raise ParameterError(message="文章不存在")
    root_comment = None
    if body.root_id > 0:
        root_comment = Comment.get_model_by_id(body.root_id)
        if root_comment is None:
            raise ParameterError(message="根评论不存在")
    if body.parent_id > 0:
        parent_comment = Comment.get_model_by_id(body.parent_id)
        if parent_comment is None:
            raise ParameterError(message="父评论不存在")
    comment = Comment(
        post_id=body.post_id,
        user_id=user.id,  # type: ignore
        root_id=body.root_id,
        parent_id=body.parent_id,
        content=body.content,
    )
    comment.save()
    if root_comment:
        root_comment.replay_count += 1
        root_comment.save()
    return Created(message="创建评论成功")
