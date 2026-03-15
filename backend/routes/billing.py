"""
商业化/计费相关 API（预埋）。

路由前缀：/api/billing

设计目标：
- 提供“套餐/订阅/权益”的最小闭环数据结构；
- 当前不对接真实支付，仅支持：
  - 查询套餐；
  - 查询当前组织权益与订阅信息；
  - 通过手动接口授予订阅（用于灰度/内测/演示）。
"""

import json
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from ..models import db, Org, OrgMember, Plan, Entitlement, PlanEntitlement, Subscription, BillingEvent
from ..utils.auth import auth_required
from ..utils.idempotency import idempotent


billing_bp = Blueprint('billing', __name__)


def _get_or_create_default_org(user):
    """
    获取或创建用户默认组织（计费维度按组织）。
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


def _ensure_seed_data():
    """
    确保基础计费配置存在（权益定义、免费套餐与其权益配置）。

    说明：
    - 这是一个“懒加载种子”逻辑，避免首次访问 API 时表为空；
    - 生产环境建议改为独立迁移/种子脚本或管理后台配置。
    """
    if Entitlement.query.count() == 0:
        db.session.add_all([
            Entitlement(key='export.enabled', type='bool', default_value='true'),
            Entitlement(key='activity.max_count', type='int', default_value='9999'),
            Entitlement(key='team.enabled', type='bool', default_value='false'),
        ])
        db.session.commit()

    if Plan.query.count() == 0:
        plan = Plan(code='free', name='免费版（预埋）', period='month', status='active', sort=0)
        db.session.add(plan)
        db.session.commit()

        db.session.add_all([
            PlanEntitlement(plan_id=plan.id, entitlement_key='export.enabled', value='true'),
            PlanEntitlement(plan_id=plan.id, entitlement_key='activity.max_count', value='9999'),
            PlanEntitlement(plan_id=plan.id, entitlement_key='team.enabled', value='false'),
        ])
        db.session.commit()


def _coerce_value(t: str, v: str):
    """
    按权益定义类型将字符串值转换为运行时可用的类型。

    参数：
    - t: 类型（bool/int/其它）
    - v: 字符串值

    返回：
    - 转换后的值（bool/int/str）
    """
    if t == 'bool':
        return str(v).lower() in ('1', 'true', 'yes', 'y')
    if t == 'int':
        try:
            return int(v)
        except Exception:
            return 0
    return v


def _compute_entitlements(org_id: int):
    """
    计算某组织在“当前时刻”的有效权益集合。

    规则：
    - 无订阅/订阅无效/过期：返回默认权益（Entitlement.default_value）
    - 订阅有效（trialing/active 且未过期）：返回套餐权益覆盖后的结果
    """
    _ensure_seed_data()
    ent_defs = Entitlement.query.all()
    result = {e.key: _coerce_value(e.type, e.default_value) for e in ent_defs}

    sub = Subscription.query.filter_by(org_id=org_id).order_by(Subscription.id.desc()).first()
    if not sub:
        return result

    now = datetime.utcnow()
    if sub.status not in ('trialing', 'active'):
        return result
    if sub.end_at and sub.end_at < now:
        return result

    rows = PlanEntitlement.query.filter_by(plan_id=sub.plan_id).all()
    defs = {e.key: e for e in ent_defs}
    for r in rows:
        d = defs.get(r.entitlement_key)
        if not d:
            continue
        result[r.entitlement_key] = _coerce_value(d.type, r.value)
    return result


@billing_bp.route('/plans', methods=['GET'])
def list_plans():
    """
    获取可用套餐列表（仅返回 status=active 的套餐）。

    返回：
    - 200: 套餐数组，每项包含 entitlements（已按定义类型转换）。
    """
    _ensure_seed_data()
    plans = Plan.query.order_by(Plan.sort.asc()).all()
    ent_defs = {e.key: e for e in Entitlement.query.all()}
    plan_ents = {}
    for pe in PlanEntitlement.query.all():
        plan_ents.setdefault(pe.plan_id, {})[pe.entitlement_key] = _coerce_value(ent_defs[pe.entitlement_key].type, pe.value) if pe.entitlement_key in ent_defs else pe.value
    return jsonify([
        {
            'id': p.id,
            'code': p.code,
            'name': p.name,
            'period': p.period,
            'status': p.status,
            'entitlements': plan_ents.get(p.id, {}),
        }
        for p in plans
        if p.status == 'active'
    ])


@billing_bp.route('/me/entitlements', methods=['GET'])
@auth_required
def my_entitlements():
    """
    获取当前登录用户所属默认组织的权益集合。

    返回：
    - 200: {org_id, entitlements}
    """
    org = _get_or_create_default_org(request.user)
    entitlements = _compute_entitlements(org.id)
    return jsonify({
        'org_id': org.id,
        'entitlements': entitlements,
    })


@billing_bp.route('/me/subscription', methods=['GET'])
@auth_required
def my_subscription():
    """
    获取当前登录用户默认组织的订阅信息（可能为空）。
    """
    org = _get_or_create_default_org(request.user)
    sub = Subscription.query.filter_by(org_id=org.id).order_by(Subscription.id.desc()).first()
    if not sub:
        return jsonify({'org_id': org.id, 'subscription': None})
    return jsonify({
        'org_id': org.id,
        'subscription': {
            'id': sub.id,
            'plan_id': sub.plan_id,
            'status': sub.status,
            'start_at': sub.start_at.isoformat() if sub.start_at else None,
            'end_at': sub.end_at.isoformat() if sub.end_at else None,
            'provider': sub.provider,
            'external_ref': sub.external_ref,
        }
    })


@billing_bp.route('/admin/manual-grant', methods=['POST'])
@auth_required
@idempotent
def manual_grant():
    """
    手动授予订阅（演示/内测用途）。

    Body（JSON）：
    - plan_code: 套餐 code（默认 free）
    - days: 有效天数（默认 30）

    返回：
    - 200: 开通成功，返回 subscription_id
    - 404: 套餐不存在
    """
    org = _get_or_create_default_org(request.user)
    data = request.get_json() or {}
    plan_code = data.get('plan_code', 'free')
    days = int(data.get('days', 30))
    _ensure_seed_data()
    plan = Plan.query.filter_by(code=plan_code).first()
    if not plan:
        return jsonify({'error': '套餐不存在'}), 404

    now = datetime.utcnow()
    sub = Subscription(
        org_id=org.id,
        plan_id=plan.id,
        status='active',
        start_at=now,
        end_at=now + timedelta(days=days),
        provider='manual',
    )
    db.session.add(sub)
    db.session.add(BillingEvent(org_id=org.id, event_type='manual_grant', payload=json.dumps({'plan_code': plan_code, 'days': days}, ensure_ascii=False)))
    db.session.commit()
    return jsonify({'message': '已开通', 'subscription_id': sub.id})
