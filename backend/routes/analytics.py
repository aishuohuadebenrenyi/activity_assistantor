"""
埋点/分析相关 API（事件上报与简单看板）。

路由前缀：/api/analytics

设计要点：
- `/events/batch` 支持匿名上报，避免“未登录埋点 -> 401 -> 前端重定向 -> 循环”的问题；
- 若请求携带有效 token，会尽力解析并关联 user/org；
- 为写入安全与重放一致性，批量上报同样接入幂等。
"""

import json
from datetime import date
from flask import Blueprint, request, jsonify, current_app
from ..models import db, Org, OrgMember, EventLog, MetricsDaily
from ..utils.auth import auth_required
from ..utils.idempotency import idempotent
from ..utils.request_id import get_request_id
import jwt


analytics_bp = Blueprint('analytics', __name__)


def _get_or_create_default_org(user):
    """
    获取或创建用户默认组织（用于把埋点归档到组织维度）。
    """
    org = Org.query.filter_by(owner_user_id=user.id).first()
    if org:
        return org
    org = Org(owner_user_id=user.id, name='默认主办方')
    db.session.add(org)
    db.session.flush()
    db.session.add(OrgMember(org_id=org.id, user_id=user.id, role='owner', status='active'))
    db.session.commit()
    return org


@analytics_bp.route('/events/batch', methods=['POST'])
@idempotent
def ingest_events():
    """
    批量接收埋点事件（匿名可用）。

    Header（可选）：
    - Authorization: Bearer <token>（若有效则尝试关联 user/org）
    - X-Client-Platform / X-App-Version / X-Device-Id：客户端环境信息

    Body（JSON）：
    - 支持两种形态：
      1) { "events": [ ... ] }
      2) [ ... ]（兼容直传数组）
    - 每个 event 可包含：
      - event_name 或 name（必填其一）
      - properties（可选，任意 JSON 对象）
      - platform/app_version/device_id（可选，覆盖 header）

    返回：
    - 200: {"accepted": <写入条数>}
    - 400: events 非 list
    """
    user = None
    org = None
    auth_header = request.headers.get('Authorization')
    if auth_header:
        try:
            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            from ..models import User
            user = User.query.get(payload.get('user_id'))
            if user:
                org = _get_or_create_default_org(user)
        except Exception:
            user = None
            org = None

    payload = request.get_json()
    events = payload.get('events') if isinstance(payload, dict) else payload
    if not isinstance(events, list):
        return jsonify({'error': 'events must be a list'}), 400

    platform = request.headers.get('X-Client-Platform', 'unknown')
    app_version = request.headers.get('X-App-Version')
    device_id = request.headers.get('X-Device-Id')
    rid = get_request_id()

    rows = []
    for e in events:
        if not isinstance(e, dict):
            continue
        name = e.get('event_name') or e.get('name')
        if not name:
            continue
        rows.append(EventLog(
            event_name=name,
            user_id=user.id if user else None,
            org_id=org.id if org else None,
            platform=e.get('platform') or platform,
            app_version=e.get('app_version') or app_version,
            device_id=e.get('device_id') or device_id,
            request_id=rid,
            properties=json.dumps(e.get('properties') or {}, ensure_ascii=False),
        ))

    if rows:
        db.session.add_all(rows)
        db.session.commit()

    return jsonify({'accepted': len(rows)})


@analytics_bp.route('/dashboard', methods=['GET'])
@auth_required
def get_dashboard():
    """
    获取简单日维度指标看板（需要登录）。

    当前实现：
    - 仅查询 `metrics_daily` 表中当天、当前组织的指标键值对；
    - 指标写入逻辑未在此版本实现，属于预留能力。
    """
    org = _get_or_create_default_org(request.user)
    today = date.today()
    metrics = MetricsDaily.query.filter_by(org_id=org.id, date=today).all()
    return jsonify({
        'org_id': org.id,
        'date': today.isoformat(),
        'metrics': {m.metric_key: m.metric_value for m in metrics},
    })
