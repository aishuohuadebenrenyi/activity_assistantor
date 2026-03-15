"""
组织/团队相关 API（预埋）。

路由前缀：/api/org

当前业务约束：
- 每个用户默认拥有一个“主办方组织”（owner_user_id 唯一）；
- 目前仅提供查看/修改组织名称与查看成员列表，用于后续团队协作与计费能力铺路。
"""

from flask import Blueprint, request, jsonify
from ..models import db, Org, OrgMember
from ..utils.auth import auth_required
from ..utils.idempotency import idempotent


org_bp = Blueprint('org', __name__)


def _get_or_create_default_org(user):
    """
    获取或创建用户的默认组织。

    参数：
    - user: 当前登录用户

    返回：
    - Org: 默认组织对象（已确保 OrgMember(owner) 存在）。
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


@org_bp.route('/me', methods=['GET'])
@auth_required
def get_my_org():
    """
    获取当前用户的默认组织信息。
    """
    org = _get_or_create_default_org(request.user)
    return jsonify({
        'id': org.id,
        'owner_user_id': org.owner_user_id,
        'name': org.name,
        'status': org.status,
        'created_at': org.created_at.isoformat(),
        'updated_at': org.updated_at.isoformat(),
    })


@org_bp.route('/me/members', methods=['GET'])
@auth_required
def list_my_org_members():
    """
    获取当前用户默认组织的成员列表。
    """
    org = _get_or_create_default_org(request.user)
    members = OrgMember.query.filter_by(org_id=org.id).all()
    return jsonify([
        {
            'id': m.id,
            'org_id': m.org_id,
            'user_id': m.user_id,
            'role': m.role,
            'status': m.status,
            'created_at': m.created_at.isoformat(),
        }
        for m in members
    ])


@org_bp.route('/me', methods=['PUT'])
@auth_required
@idempotent
def update_my_org():
    """
    更新当前用户默认组织（目前仅支持修改 name）。

    Body（JSON）：
    - name: 组织名称（可选，不传则不修改）
    """
    org = _get_or_create_default_org(request.user)
    data = request.get_json() or {}
    name = data.get('name')
    if name:
        org.name = name
        db.session.commit()
    return jsonify({
        'id': org.id,
        'owner_user_id': org.owner_user_id,
        'name': org.name,
        'status': org.status,
        'created_at': org.created_at.isoformat(),
        'updated_at': org.updated_at.isoformat(),
    })
