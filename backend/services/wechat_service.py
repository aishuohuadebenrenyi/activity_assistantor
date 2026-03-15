import requests
import json
import base64
from flask import current_app

class WeChatService:
    @staticmethod
    def get_access_token():
        """
        Get WeChat Access Token.
        In production, this should be cached (Redis/DB) for 7200s.
        """
        appid = current_app.config.get('WECHAT_APPID')
        secret = current_app.config.get('WECHAT_SECRET')
        
        # Mock for development if no real config
        if not appid or 'mock' in appid:
            return "mock_access_token"

        url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={secret}"
        try:
            resp = requests.get(url)
            data = resp.json()
            if 'access_token' in data:
                return data['access_token']
            else:
                print(f"WeChat Token Error: {data}")
                return None
        except Exception as e:
            print(f"WeChat Token Exception: {e}")
            return None

    @staticmethod
    def generate_url_link(path, query="", is_expire=True, expire_type=1, expire_interval=30):
        """
        Generate URL Link (https://wxaurl.cn/...)
        """
        token = WeChatService.get_access_token()
        if not token:
            return None
            
        if token == "mock_access_token":
            return f"https://wxaurl.cn/mock_link?path={path}&query={query}"

        url = f"https://api.weixin.qq.com/wxa/generate_urllink?access_token={token}"
        payload = {
            "path": path,
            "query": query,
            "is_expire": is_expire,
            "expire_type": expire_type,
            "expire_interval": expire_interval
        }
        
        try:
            resp = requests.post(url, json=payload)
            data = resp.json()
            if data.get('errcode') == 0:
                return data.get('url_link')
            else:
                print(f"URL Link Error: {data}")
                return None
        except Exception as e:
            print(f"URL Link Exception: {e}")
            return None

    @staticmethod
    def get_unlimited_qrcode(scene, page="pages/index/index", width=430):
        """
        Get Unlimited Mini Program Code (Buffer/Base64)
        """
        token = WeChatService.get_access_token()
        if not token:
            return None

        # Mock Image for development
        if token == "mock_access_token":
            # Return a simple 1x1 black pixel base64 or similar placeholder
            return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+P+/HgAFhAJ/wlseKgAAAABJRU5ErkJggg=="

        url = f"https://api.weixin.qq.com/wxa/getwxacodeunlimit?access_token={token}"
        payload = {
            "scene": scene,
            "page": page,
            "width": width,
            "check_path": False, # Set to True in production if page exists
            "env_version": "develop" # release, trial, develop
        }
        
        try:
            resp = requests.post(url, json=payload)
            # If successful, content-type is image/jpeg or image/png
            if resp.headers.get('Content-Type', '').startswith('image'):
                # Convert to base64
                b64_data = base64.b64encode(resp.content).decode('utf-8')
                return f"data:image/jpeg;base64,{b64_data}"
            else:
                print(f"QRCode Error: {resp.text}")
                return None
        except Exception as e:
            print(f"QRCode Exception: {e}")
            return None

    @staticmethod
    def get_openid(code):
        """
        Convert JS Code to OpenID (Mini Program Login)
        """
        appid = current_app.config.get('WECHAT_APPID')
        secret = current_app.config.get('WECHAT_SECRET')
        
        if not appid or 'mock' in appid:
            # Mocking openid based on code
            return f"mock_openid_{code}"

        url = f"https://api.weixin.qq.com/sns/jscode2session?appid={appid}&secret={secret}&js_code={code}&grant_type=authorization_code"
        try:
            resp = requests.get(url)
            data = resp.json()
            if 'openid' in data:
                return data['openid']
            else:
                print(f"WeChat OpenID Error: {data}")
                return None
        except Exception as e:
            print(f"WeChat OpenID Exception: {e}")
            return None

    @staticmethod
    def check_content_security(content):
        """
        WeChat Message Security Check (msgSecCheck)
        """
        token = WeChatService.get_access_token()
        if not token:
            return True # If cannot get token, fail-safe or handle error?

        if token == "mock_access_token":
            # Simple keyword mock check for development
            bad_keywords = ["敏感词", "违禁品", "政治"]
            for word in bad_keywords:
                if word in content:
                    return False
            return True

        url = f"https://api.weixin.qq.com/wxa/msg_sec_check?access_token={token}"
        payload = {
            "version": 2,
            "openid": "OPENID", # Recommended for better accuracy in v2
            "scene": 2, # 2 for social/comment
            "content": content
        }
        
        try:
            resp = requests.post(url, json=payload)
            data = resp.json()
            # result.suggest == "pass" means OK
            if data.get('result', {}).get('suggest') == "pass":
                return True
            else:
                print(f"Content Security Error: {data}")
                return False
        except Exception as e:
            print(f"Content Security Exception: {e}")
            return True # Fail-safe
