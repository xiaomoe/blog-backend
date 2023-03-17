from flask import Blueprint
from src.common.cos import cos

bp = Blueprint("upload", __name__, url_prefix="/file")


@bp.route("/token")
def get_qcloud_token():
    res = cos.get_credential()
    return res
