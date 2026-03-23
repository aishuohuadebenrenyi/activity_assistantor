"""
短信服务封装（验证码发送）。

支持两种模式：
1. Mock 模式（开发/测试）：仅打印日志，不发送真实短信
2. 生产模式：集成阿里云短信 SDK

配置项（环境变量）：
- ALIYUN_SMS_ACCESS_KEY_ID: 阿里云 AccessKey ID
- ALIYUN_SMS_ACCESS_KEY_SECRET: 阿里云 AccessKey Secret
- ALIYUN_SMS_SIGN_NAME: 短信签名名称
- ALIYUN_SMS_TEMPLATE_CODE: 短信模板 CODE
"""

from flask import current_app
import random
import os
import json

class SmsService:
    """
    短信服务封装类。
    
    生产环境需配置阿里云短信服务：
    1. 开通阿里云短信服务
    2. 申请短信签名和模板
    3. 配置环境变量
    """
    
    @staticmethod
    def _is_production():
        """
        判断是否为生产环境。
        
        当配置了阿里云短信凭证时，视为生产环境。
        """
        return bool(os.environ.get('ALIYUN_SMS_ACCESS_KEY_ID') and 
                   os.environ.get('ALIYUN_SMS_ACCESS_KEY_SECRET'))
    
    @staticmethod
    def send_code(phone, code):
        """
        发送短信验证码。

        参数：
        - phone: 接收验证码的手机号
        - code: 验证码字符串

        返回：
        - bool: 是否发送成功
        """
        if SmsService._is_production():
            return SmsService._send_aliyun_sms(phone, code)
        else:
            return SmsService._send_mock(phone, code)
    
    @staticmethod
    def _send_mock(phone, code):
        """
        Mock 发送（开发/测试环境）。
        
        仅打印日志，模拟发送成功。
        """
        print(f"[SMS MOCK] 发送验证码到 {phone}: {code}")
        print(f"[SMS MOCK] 验证码有效期: 5 分钟")
        return True
    
    @staticmethod
    def _send_aliyun_sms(phone, code):
        """
        阿里云短信发送（生产环境）。
        
        使用阿里云短信 SDK 发送验证码。
        """
        try:
            from aliyunsdkcore.client import AcsClient
            from aliyunsdkcore.acs_exception.exceptions import ServerException
            from aliyunsdkdysmsapi.request.v20170525.SendSmsRequest import SendSmsRequest
            
            access_key_id = os.environ.get('ALIYUN_SMS_ACCESS_KEY_ID')
            access_key_secret = os.environ.get('ALIYUN_SMS_ACCESS_KEY_SECRET')
            sign_name = os.environ.get('ALIYUN_SMS_SIGN_NAME', '活动帮手')
            template_code = os.environ.get('ALIYUN_SMS_TEMPLATE_CODE')
            
            client = AcsClient(access_key_id, access_key_secret, 'cn-hangzhou')
            
            request = SendSmsRequest()
            request.set_PhoneNumbers(phone)
            request.set_SignName(sign_name)
            request.set_TemplateCode(template_code)
            request.set_TemplateParam(json.dumps({'code': code}))
            
            response = client.do_action_with_exception(request)
            result = json.loads(response.decode('utf-8'))
            
            if result.get('Code') == 'OK':
                print(f"[SMS] 验证码发送成功: {phone}")
                return True
            else:
                print(f"[SMS] 验证码发送失败: {result}")
                return False
                
        except ImportError:
            print("[SMS ERROR] 阿里云 SDK 未安装，请执行: pip install aliyun-python-sdk-core aliyun-python-sdk-dysmsapi")
            return False
        except ServerException as e:
            print(f"[SMS ERROR] 阿里云服务异常: {e}")
            return False
        except Exception as e:
            print(f"[SMS ERROR] 发送异常: {e}")
            return False
        
    @staticmethod
    def generate_code():
        """
        生成 6 位随机验证码。

        返回：
        - str: 6 位数字字符串
        """
        return str(random.randint(100000, 999999))
