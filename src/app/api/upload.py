from flask import Blueprint
from src.common.cos import cos

bp = Blueprint("upload", __name__, url_prefix="/file")


@bp.get("/token")
def get_qcloud_token() -> dict[str, str]:
    return cos.get_credential()
