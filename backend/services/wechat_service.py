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
