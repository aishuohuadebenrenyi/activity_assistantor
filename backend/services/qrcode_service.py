"""
二维码生成服务。

职责：
- 生成签到二维码图片（Base64 格式）；
- 支持自定义尺寸与样式。

依赖：
- qrcode: 二维码生成库
- Pillow: 图像处理库
"""

import qrcode
from qrcode.image.pil import PilImage
import base64
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

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
    生成签到二维码。

    参数：
    - activity_id: 活动 ID
    - registration_id: 报名记录 ID
    - timestamp: 时间戳

    返回：
    - tuple[str, str]: (签到码内容, Base64 图片数据)
    """
    code_content = f"CHECKIN:{activity_id}:{registration_id}:{timestamp}"
    b64_code = base64.b64encode(code_content.encode('utf-8')).decode('utf-8')
    
    qr_base64 = generate_qrcode_base64(code_content)
    
    return b64_code, qr_base64
