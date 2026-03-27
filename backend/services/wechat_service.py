import requests
import json
import base64
import time
import logging
from flask import current_app
from threading import Lock

logger = logging.getLogger(__name__)

class WeChatService:
    """
    微信能力封装（小程序登录、内容安全、分享链接与小程序码）。
    
    优化内容：
    - 添加 access_token 缓存机制，避免频繁调用微信 API
    - 添加线程锁防止并发请求
    - 缓存有效期 7200 秒，提前 300 秒刷新
    """
    
    _access_token_cache = {
        'token': None,
        'expires_at': 0
    }
    _token_lock = Lock()
    
    @classmethod
    def get_access_token(cls):
        """
        获取微信 access_token（带缓存）。
        
        缓存策略：
        - 有效期 7200 秒，提前 300 秒刷新
        - 使用线程锁防止并发请求
        
        返回：
        - str | None: access_token 字符串；获取失败返回 None。
        """
        now = time.time()
        
        if cls._access_token_cache['token'] and cls._access_token_cache['expires_at'] > now:
            logger.debug(f"[WECHAT] Using cached access_token, expires in {cls._access_token_cache['expires_at'] - now:.0f}s")
            return cls._access_token_cache['token']
        
        with cls._token_lock:
            if cls._access_token_cache['token'] and cls._access_token_cache['exists_at'] > now:
                return cls._access_token_cache['token']
            
            token = cls._fetch_access_token()
            if token:
                cls._access_token_cache['token'] = token
                cls._access_token_cache['expires_at'] = now + 7200 - 300
                logger.info(f"[WECHAT] access_token cached, expires in {7200 - 300}s")
            
            return token
    
    @classmethod
    def _fetch_access_token(cls):
        """
        实际请求微信 API 获取 token。
        
        返回：
        - str | None: access_token 或 None
        """
        appid = current_app.config.get('WECHAT_APPID')
        secret = current_app.config.get('WECHAT_SECRET')
        
        if not appid or 'mock' in appid:
            logger.debug("[WECHAT] Using mock access_token (no real config)")
            return "mock_access_token"

        url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={secret}"
        try:
            logger.info("[WECHAT] Fetching access_token from WeChat API")
            resp = requests.get(url, timeout=10)
            data = resp.json()
            if 'access_token' in data:
                logger.info("[WECHAT] access_token obtained successfully")
                return data['access_token']
            else:
                logger.error(f"[WECHAT] Token API error: {data}")
                return None
        except Exception as e:
            logger.error(f"[WECHAT] Token API exception: {e}")
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
            logger.info(f"[WECHAT] Generating URL Link for path={path}")
            resp = requests.post(url, json=payload, timeout=10)
            data = resp.json()
            if data.get('errcode') == Данные обрезаются... (слишком длинный контент)
