import requests
import json
import base64
from flask import current_app

class WeChatService:
    """
    微信能力封装（小程序登录、内容安全、分享链接与小程序码）。

    当前实现策略：
    - 若未配置真实 WECHAT_APPID/WECHAT_SECRET（或处于 mock 配置），返回 mock 结果便于本地开发；
    - 生产环境需对 access_token 做缓存（有效期 7200s），并处理接口失败与重试。
    """
    @staticmethod
    def get_access_token():
        """
        获取微信 access_token。

        返回：
        - str | None: access_token 字符串；获取失败返回 None。

        生产建议：
        - access_token 需缓存（Redis/DB），避免频繁调用导致限流；
        - 并发获取时建议加锁/单飞，避免缓存击穿。
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
        生成微信 URL Link（用于分享/拉起小程序）。

        参数：
        - path: 小程序页面路径（如 pages/activity/detail/detail）
        - query: querystring（如 id=123）
        - is_expire/expire_type/expire_interval: 过期策略参数（透传微信接口）

        返回：
        - str | None: url_link；若失败返回 None；mock 模式下返回可读的占位链接。
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
        获取小程序码（无数量限制）。

        参数：
        - scene: 场景参数（建议使用短字符串，如 id=123）
        - page: 目标页面路径
        - width: 图片宽度

        返回：
        - str | None: DataURL（data:image/...;base64,xxxx）；失败返回 None。
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
        使用微信登录 code 换取 openid（小程序登录）。

        参数：
        - code: 小程序登录返回的 code

        返回：
        - str | None: openid；失败返回 None；mock 模式下返回 mock_openid_<code>。
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
        微信内容安全校验（msgSecCheck）。

        参数：
        - content: 待检测文本内容

        返回：
        - bool: 是否通过（True 通过，False 命中违规）

        说明：
        - mock 模式下使用关键词匹配模拟拦截；
        - 真实接口若异常，当前实现采取 fail-safe（返回 True），以避免因微信接口波动影响业务可用性；
          生产环境可按合规要求改为 fail-closed（接口异常时拒绝发布）。
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
