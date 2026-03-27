import hashlib
import json
import logging
from functools import wraps
from flask import request, make_response
from ..models import db, IdempotencyKey
from .errors import error_response

logger = logging.getLogger(__name__)


def _hash_request(method: str, path: str, body) -> str:
    """
    计算一次“写请求”的指纹哈希，用于幂等冲突检测。

    幂等语义：
    - 同一个 Idempotency-Key 在首次成功写入后，会保存该请求的 method/path/body 哈希与响应；
    - 之后客户端携带同一 key 再次请求时：
      - 若 method/path/body 与首次一致：直接返回首次响应（replay）；
      - 若不一致：返回 409 并提示“幂等键冲突”，避免把同一个 key 用在不同语义的写操作上。

    参数：
    - method: HTTP 方法（已转大写）。
    - path: 请求路径（如 /api/activities/1/register）。
    - body: JSON body（dict/list/None）。

    返回：
    - str: sha256 十六进制摘要。
    """
    raw = json.dumps({"method": method, "path": path, "body": body}, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def idempotent(f):
    """
    写接口幂等装饰器（基于 `Idempotency-Key` 请求头）。

    适用场景：
    - 端侧弱网/断网重试；
    - 前端离线队列重放；
    - 用户重复点击导致的重复提交。

    行为：
    - 未携带 `Idempotency-Key`：不启用幂等（原样执行）；
    - 首次请求：执行原函数并将响应序列化存入 `idempotency_keys`；
    - 重放请求：若指纹一致，直接返回首次响应，并加响应头 `Idempotent-Replay: 1`。

    注意：
    - 当前实现仅在响应可 JSON 化时才会持久化；否则直接返回原响应。
    - 该表会持续增长；生产环境建议增加 TTL/归档策略（例如按 created_at 清理）。
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get("Idempotency-Key")
        if not key:
            return f(*args, **kwargs)

        body = request.get_json(silent=True)
        method = request.method.upper()
        path = request.path
        request_hash = _hash_request(method, path, body)
        user_id = getattr(getattr(request, "user", None), "id", None)

        existing = IdempotencyKey.query.filter_by(key=key).first()
        if existing:
            if existing.method != method or existing.path != path or existing.request_hash != request_hash:
                logger.warning(f"[IDEMPOTENCY] Key conflict: key={key[:16]}..., path={path}, user_id={user_id}")
                return error_response("IDEMPOTENCY_CONFLICT", "幂等键冲突", status=409)
            logger.info(f"[IDEMPOTENCY] Replay response: key={key[:16]}..., path={path}, status={existing.response_status}")
            resp = make_response(existing.response_body, existing.response_status)
            resp.headers["Content-Type"] = "application/json; charset=utf-8"
            resp.headers["Idempotent-Replay"] = "1"
            return resp

        result = f(*args, **kwargs)
        resp = make_response(result)
        try:
            body_json = resp.get_json()
            response_body = json.dumps(body_json, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        except Exception:
            return resp

        record = IdempotencyKey(
            key=key,
            user_id=user_id,
            method=method,
            path=path,
            request_hash=request_hash,
            response_status=resp.status_code,
            response_body=response_body,
        )
        db.session.add(record)
        db.session.commit()
        logger.debug(f"[IDEMPOTENCY] Key saved: key={key[:16]}..., path={path}, status={resp.status_code}")
        return resp

    return decorated
