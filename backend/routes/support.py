"""
用户支持/客服相关 API（预埋）。

路由前缀：/api/support

目的：
- 给前端提供统一的“客服入口配置”与“会话留痕”能力；
- 便于后续接入企业微信客服/工单系统/自建客服系统。
"""

import json
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from ..models import db, Org, OrgMember, SupportSession
from ..utils.auth import auth_required
from ..utils.idempotency import idempotent


support_bp = Blueprint('support', __name__)


def _get_or_create_default_org(user):
    """
    获取或创建用户默认组织（客服会话按组织归档）。
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


@support_bp.route('/entry', methods=['GET'])
@auth_required
def get_support_entry():
    """
    获取客服入口配置与上下文信息（需要登录）。

    Query 参数：
    - scene: 进入客服的场景标识（如 feedback/profile/activity_detail），默认 unknown
    - platform: 平台标识（可选；不传则使用请求头 X-Client-Platform）

    返回：
    - customer_service_url: 客服链接（来自配置 CUSTOMER_SERVICE_URL，可为空字符串）
    - context_token: 一次性的上下文 token（便于后续与第三方系统关联）
    - context: 结构化上下文（user_id/org_id/scene/platform/app_version）
    """
    user = request.user
    org = _get_or_create_default_org(user)
    scene = request.args.get('scene', 'unknown')
    platform = request.args.get('platform', request.headers.get('X-Client-Platform', 'unknown'))

    context = {
        'user_id': user.id,
        'org_id': org.id,
        'scene': scene,
        'platform': platform,
        'app_version': request.headers.get('X-App-Version'),
    }
    context_token = str(uuid.uuid4())

    url = current_app.config.get('CUSTOMER_SERVICE_URL') or ''

    return jsonify({
        'customer_service_url': url,
        'context_token': context_token,
        'context': context,
    })


@support_bp.route('/session', methods=['POST'])
@auth_required
@idempotent
def record_support_session():
    """
    记录客服会话事件（需要登录）。

    Body（JSON）：
    - status: opened/closed 等（默认 opened）
    - platform: 平台标识（默认取请求头 X-Client-Platform）
    - entry_point: 入口标识（默认 unknown）
    - external_session_id/category/satisfaction/first_response_ms/context_snapshot: 可选字段

    业务规则：
    - 当 status=closed 时自动写入 closed_at；
    - 使用幂等避免离线重放重复写入。

    返回：
    - 200: {message: "ok", session_id}
    """
    user = request.user
    org = _get_or_create_default_org(user)
    data = request.get_json() or {}

    status = data.get('status', 'opened')
    platform = data.get('platform', request.headers.get('X-Client-Platform', 'unknown'))
    entry_point = data.get('entry_point', 'unknown')

    sess = SupportSession(
        user_id=user.id,
        org_id=org.id,
        platform=platform,
        entry_point=entry_point,
        status=status,
        opened_at=datetime.utcnow(),
        external_session_id=data.get('external_session_id'),
        category=data.get('category'),
        satisfaction=data.get('satisfaction'),
        first_response_ms=data.get('first_response_ms'),
        context_snapshot=json.dumps(data.get('context_snapshot', {}), ensure_ascii=False),
    )
    if status == 'closed':
        sess.closed_at = datetime.utcnow()

    db.session.add(sess)
    db.session.commit()

    return jsonify({'message': 'ok', 'session_id': sess.id})
