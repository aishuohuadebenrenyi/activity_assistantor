from flask import current_app
import random

class SmsService:
    """
    短信服务封装（验证码发送）。

    当前实现为开发/演示用的 Mock：
    - 仅打印发送日志并返回成功；
    - 生产环境应替换为阿里云/腾讯云等短信 SDK，并处理签名、模板、频控与失败重试。
    """
    @staticmethod
    def send_code(phone, code):
        """
        发送短信验证码。

        参数：
        - phone: 接收验证码的手机号
        - code: 验证码字符串

        返回：
        - bool: 是否发送成功（当前实现恒为 True）
        """
        # In real production, integrate with Alibaba Cloud or Tencent Cloud SDK
        # Example for Alibaba Cloud:
        # client = AcsClient(access_key_id, access_key_secret, 'cn-hangzhou')
        # request = SendSmsRequest.SendSmsRequest()
        # request.set_TemplateCode(template_code)
        # request.set_TemplateParam(json.dumps({'code': code}))
        # request.set_PhoneNumbers(phone)
        # response = client.do_action_with_exception(request)
        
        # Current implementation: Structured Mock for development
        print(f"DEBUG: [SMS SERVICE] Sending verification code {code} to {phone}")
        
        # Simulating successful delivery
        return True
        
    @staticmethod
    def generate_code():
        """
        生成 6 位随机验证码。

        返回：
        - str: 6 位数字字符串
        """
        return str(random.randint(100000, 999999))
