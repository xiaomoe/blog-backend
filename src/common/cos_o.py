from typing import TypedDict

from sts.sts import Sts

from src.config import config


class COSConfig(TypedDict):
    url: str
    domain: str | None  # 域名 默认为 sts.tencentcloudapi.com
    secret_id: str
    secret_key: str  # 固定密钥
    duration_seconds: int | None  # 临时密钥有效时长(秒) 默认 1800 半小时, 最大 7200 两小时
    bucket: str  # 存储桶名称: bucketName-appid
    region: str  # 存储桶所在地区: ap-beijing
    allow_prefix: list[str]  # 有权访问的资源前缀: ["a/*", "a.jpg", "*"]
    allow_actions: list[str]  # 密钥的权限列表


class Credentials(TypedDict):
    tmpSecretId: str  # noqa
    tmpSecretKey: str  # noqa
    sessionToken: str  # noqa


class COSResult(TypedDict):
    credentials: Credentials
    startTime: str  # noqa
    expiredTime: str  # noqa


class COS:
    """获取临时凭证(使用官方 SDK)

    更多介绍: https://cloud.tencent.com/document/product/1312/48195
    https://github.com/tencentyun/qcloud-cos-sts-sdk/blob/master/python/README.md
    """

    cos_config: COSConfig

    def __init__(self) -> None:
        self.cos_config = {
            "url": "https://sts.tencentcloudapi.com/",
            "domain": "sts.tencentcloudapi.com",
            "duration_seconds": 1800,  # 半小时
            "secret_id": config.COS_SECRET_ID,
            "secret_key": config.COS_SECRET_KEY,
            "bucket": config.COS_BUCKET,
            "region": config.COS_REGION,
            "allow_prefix": ["*"],
            "allow_actions": [  # 其他权限列表请看 https://cloud.tencent.com/document/product/436/31923
                # 简单上传
                "name/cos:PutObject",
                "name/cos:PostObject",
                # 分片上传
                "name/cos:InitiateMultipartUpload",
                "name/cos:ListMultipartUploads",
                "name/cos:ListParts",
                "name/cos:UploadPart",
                "name/cos:CompleteMultipartUpload",
            ],
        }

    def get_token(self) -> COSResult:
        try:
            sts = Sts(self.cos_config)
            response = sts.get_credential()
            return response  # type: ignore
        except Exception as e:
            raise e


if __name__ == "__main__":
    cos = COS()
    print(cos.get_token())
