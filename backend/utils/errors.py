from flask import jsonify
from .request_id import get_request_id


def error_response(code: str, message: str, status: int = 400, details=None):
    """
    构造统一的 API 错误响应（JSON）。

    设计目标：
    - 让前端可以稳定地用 `ok/code/message/request_id` 判断与展示错误；
    - 保留 `request_id` 便于日志与链路排查；
    - 允许通过 `details` 承载调试/字段级错误信息（避免放敏感数据）。

    参数：
    - code: 机器可读的错误码（如 AUTH_UNAUTHORIZED、REQ_INVALID）。
    - message: 面向用户/开发者的错误说明。
    - status: HTTP 状态码（默认 400）。
    - details: 可选的结构化错误详情（dict/list/str 等）。

    返回：
    - (Response, int): Flask 的 JSON 响应对象与 HTTP 状态码。
    """
    payload = {
        "ok": False,
        "code": code,
        "message": message,
        "error": message,
        "request_id": get_request_id(),
    }
    if details is not None:
        payload["details"] = details
    return jsonify(payload), status
