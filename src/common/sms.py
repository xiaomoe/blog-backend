from structlog import getLogger
from structlog.stdlib import BoundLogger
from tencentcloud.common import credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.sms.v20210111 import models, sms_client
from wakaq.exceptions import WakaQError

from src.config import config

logger: BoundLogger = getLogger("sms")


class SMS:
    """腾讯云短信服务.

    https://cloud.tencent.com/document/product/382/43196
    """

    cred = credential.Credential(config.SMS_SECRET_ID, config.SMS_SECRET_KEY)

    client = sms_client.SmsClient(cred, "ap-guangzhou")

    request = models.SendSmsRequest()
    request.SmsSdkAppId = config.SMS_APP_ID
    request.SignName = config.SMS_SIGN_NAME
    request.TemplateId = config.SMS_TEMPLATE

    @classmethod
    def send(cls, phone: str, code: str, expire: int | None = None) -> bool:
        """发送短信.

        Args:
            phone (str): 单个手机号
            expire (int): 过期时间(秒)
            code (str): 验证码


        Returns:
            bool: 是否发送成功

        Notes:
            模板内容: ['验证码', '有效分钟数']
            response: {
                "SendStatusSet": [{
                    "SerialNo": "xxxx:xxxxxxx",
                    "PhoneNumber": "+861xxxxxxxxxx",
                    "Fee": 1,
                    "SessionContext": "",
                    "Code": "Ok",
                    "Message": "send success",
                    "IsoCode": "CN"
                }],
                "RequestId": "xxxx"
            }
        """
        _expire = ""
        if expire is None:
            _expire = "5"  # 默认5分钟
        if isinstance(expire, int):
            _expire = str(int(expire / 60))  # 传入的是秒转换成分钟
        data = [code, _expire]
        cls.request.PhoneNumberSet = [phone]
        cls.request.TemplateParamSet = data
        try:
            resp = cls.client.SendSms(cls.request)
            if resp.SendStatusSet is None or len(resp.SendStatusSet) == 0:
                return False
            code = resp.SendStatusSet[0].Code
            if code == "Ok":
                return True
            raise WakaQError()
        except TencentCloudSDKException as e:
            logger.error(str(e))
            raise Exception(f"短信服务异常: {e}") from None
