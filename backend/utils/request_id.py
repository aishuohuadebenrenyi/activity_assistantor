import uuid
from flask import g, request


def get_request_id() -> str:
    """
    获取当前请求的 request_id（用于链路追踪与问题定位）。

    规则：
    - 优先复用 `g.request_id`（同一次请求内保持不变）；
    - 若请求头包含 `X-Request-Id`，则使用该值（便于前端/网关透传）；
    - 否则生成新的 UUID。

    返回：
    - str: 本次请求的 request_id。
    """
    rid = getattr(g, "request_id", None)
    if rid:
        return rid
    rid = request.headers.get("X-Request-Id") or str(uuid.uuid4())
    g.request_id = rid
    return rid


def init_request_id(app):
    """
    将 request_id 注入到 Flask 应用的请求生命周期中。

    行为：
    - before_request：确保尽早生成/读取 request_id，便于后续日志关联；
    - after_request：把 request_id 回传到响应头 `X-Request-Id`，实现端到端追踪。

    参数：
    - app: Flask 应用实例。
    """
    @app.before_request
    def _set_request_id():
        get_request_id()

    @app.after_request
    def _attach_request_id(resp):
        resp.headers["X-Request-Id"] = get_request_id()
        return resp
