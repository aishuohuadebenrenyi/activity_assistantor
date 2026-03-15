from flask import current_app
import random

class SmsService:
    @staticmethod
    def send_code(phone, code):
        """
        Send verification code via SMS.
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
        """Generate a 6-digit random code"""
        return str(random.randint(100000, 999999))
