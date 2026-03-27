"""
二维码生成服务。

职责：
- 生成签到二维码图片（Base64 格式）；
- 支持自定义尺寸与样式；
- 使用 HMAC 签名确保签到码安全性。

依赖：
- qrcode: 二维码生成库
- Pillow: 图像处理库
"""

import qrcode
from qrcode.image.pil import PilImage
import base64
from io import BytesIO
import logging
import hmac
import hashlib
import time
import os

logger = logging.getLogger(__name__)

QR_SECRET_KEY = os.environ.get('QR_SECRET_KEY', 'zentro-default-secret-key-change-in-production')
QR_EXPIRE_SECONDS = 3600 * 24 * 7

def generate_signature(activity_id: int, registration_id: int, timestamp: int) -> str:
    """
    生成 HMAC 签名。
    
    参数：
    - activity_id: 活动 ID
    - registration_id: 报名记录 ID
    - timestamp: 时间戳
    
    返回：
    - str: HMAC 签名（16进制字符串）
    """
    message = f"{activity_id}:{registration_id}:{timestamp}"
    signature = hmac.new(
        QR_SECRET_KEY.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()[:16]
    return signature

def verify_signature(activity_id: int, registration_id: int, timestamp: int, signature: str) -> tuple[bool, str]:
    """
    验证 HMAC 签名。
    
    参数：
    - activity_id: 活动 ID
    - registration_id: 报名记录 ID
    - timestamp: 时间戳
    - signature: 待验证的签名
    
    返回：
    - tuple[bool, str]: (是否验证通过, 错误信息)
    """
    current_time = int(time.time())
    
    if current_time - timestamp > QR_EXPIRE_SECONDS:
        return False, "签到码已过期"
    
    if timestamp > current_time + 300:
        return False, "签到码时间异常"
    
    expected_signature = generate_signature(activity_id, registration_id, timestamp)
    
    if not hmac.compare_digest(expected_signature, signature):
        return False, "签到码签名无效"
    
    return True, ""

def generate_qrcode_base64(data: str, size: int = 200) -> str:
    """
    生成二维码并返回 Base64 编码的图片数据。

    参数：
    - data: 二维码内容（如签到码）
    - size: 图片尺寸（像素），默认 200x200

    返回：
    - str: Base64 编码的图片数据（data:image/png;base64,...）
    """
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=2,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return f"data:image/png;base64,{img_base64}"
    except Exception as e:
        logger.error(f"Generate QR code failed: {e}")
        return ""

def generate_checkin_qrcode(activity_id: int, registration_id: int, timestamp: int) -> tuple[str, str]:
    """
    生成签到二维码（带 HMAC 签名）。

    参数：
    - activity_id: 活动 ID
    - registration_id: 报名记录 ID
    - timestamp: 时间戳

    返回：
    - tuple[str, str]: (签到码内容, Base64 图片数据)
    """
    signature = generate_signature(activity_id, registration_id, timestamp)
    
    code_content = f"CHECKIN:{activity_id}:{registration_id}:{timestamp}:{signature}"
    b64_code = base64.b64encode(code_content.encode('utf-8')).decode('utf-8')
    
    qr_base64 = generate_qrcode_base64(code_content)
    
    return b64_code, qr_base64
