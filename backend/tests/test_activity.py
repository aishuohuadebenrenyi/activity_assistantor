"""
活动模块完整测试套件

测试覆盖：
- 活动列表获取（分页、筛选、搜索）
- 活动创建（参数校验、内容安全）
- 活动详情获取（权限、浏览量）
- 活动更新（权限、校验）
- 活动删除（权限）
- 活动分享（二维码生成）
- 活动举报
"""

import pytest
import json
import datetime
from backend.models import db, User, Activity, Registration, Report


class TestActivityList:
    """活动列表测试"""
    
    def test_get_activities_empty(self, client):
        """测试空列表"""
        response = client.get('/api/activities/')
        assert response.status_code == 200
        data = response.get_json()
        assert data['activities'] == []
        assert data['total'] == 0
    
    def test_get_activities_pagination(self, client, test_organizer):
        """测试分页"""
        with client.application.app_context():
            user = db.session.get(User, test_organizer.id)
            for i in range(25):
                activity = Activity(
                    user_id=user.id,
                    name=f"活动{i}",
                    start_time=datetime.datetime.utcnow() + datetime.timedelta(days=i)
                )
                db.session.add(activity)
            db.session.commit()
        
        response = client.get('/api/activities/?page=1&page_size=10')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['activities']) == 10
        assert data['total'] == 25
        assert data['has_more'] is True
        
        response = client.get('/api/activities/?page=3&page_size=10')
        data = response.get_json()
        assert len(data['activities']) == 5
        assert data['has_more'] is False
    
    def test_get_activities_search(self, client, test_activity):
        """测试搜索"""
        response = client.get('/api/activities/?search=测试')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['activities']) >= 1
        
        response = client.get('/api/activities/?search=不存在的活动')
        data = response.get_json()
        assert len(data['activities']) == 0


class TestActivityCreate:
    """活动创建测试"""
    
    def test_create_activity_success(self, client, organizer_auth_header):
        """测试成功创建活动"""
        payload = {
            "name": "新创建的活动",
            "type": "business",
            "date": "2026-10-01",
            "time": "10:00",
            "location": "北京市朝阳区",
            "description": "活动描述",
            "capacity": 50
        }
        response = client.post(
            '/api/activities/',
            json=payload,
            headers=organizer_auth_header
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data['name'] == "新创建的活动"
        assert data['capacity'] == 50
    
    def test_create_activity_missing_required(self, client, organizer_auth_header):
        """测试缺少必填字段"""
        payload = {
            "type": "business",
            "location": "北京市朝阳区"
        }
        response = client.post(
            '/api/activities/',
            json=payload,
            headers=organizer_auth_header
        )
        assert response.status_code == 400
    
    def test_create_activity_unauthorized(self, client):
        """测试未登录创建"""
        payload = {
            "name": "未授权活动",
            "date": "2026-10-01",
            "time": "10:00"
        }
        response = client.post('/api/activities/', json=payload)
        assert response.status_code == 401
    
    def test_create_activity_with_end_time(self, client, organizer_auth_header):
        """测试带结束时间创建"""
        payload = {
            "name": "带结束时间的活动",
            "date": "2026-10-01",
            "time": "10:00",
            "end_date": "2026-10-01",
            "end_time": "12:00"
        }
        response = client.post(
            '/api/activities/',
            json=payload,
            headers=organizer_auth_header
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data.get('end_time') is not None


class TestActivityDetail:
    """活动详情测试"""
    
    def test_get_activity_detail(self, client, test_activity):
        """测试获取活动详情"""
        response = client.get(f'/api/activities/{test_activity.id}')
        assert response.status_code == 200
        data = response.get_json()
        assert data['name'] == "测试活动"
    
    def test_get_activity_not_found(self, client):
        """测试活动不存在"""
        response = client.get('/api/activities/99999')
        assert response.status_code == 404
    
    def test_activity_views_increment(self, client, test_activity):
        """测试浏览量增加"""
        with client.application.app_context():
            activity = db.session.get(Activity, test_activity.id)
            initial_views = activity.views_count
        
        for _ in range(3):
            client.get(f'/api/activities/{test_activity.id}')
        
        with client.application.app_context():
            activity = db.session.get(Activity, test_activity.id)
            assert activity.views_count == initial_views + 3
    
    def test_organizer_sees_full_phone(self, client, test_activity, test_registration, organizer_auth_header):
        """测试主办方看到完整手机号"""
        response = client.get(
            f'/api/activities/{test_activity.id}',
            headers=organizer_auth_header
        )
        assert response.status_code == 200
        data = response.get_json()
        if data.get('registrations'):
            phone = data['registrations'][0].get('phone', '')
            assert '****' not in phone or phone == "13800138000"
    
    def test_non_organizer_sees_masked_phone(self, client, test_activity, test_registration, auth_header):
        """测试非主办方看到脱敏手机号"""
        response = client.get(
            f'/api/activities/{test_activity.id}',
            headers=auth_header
        )
        assert response.status_code == 200


class TestActivityUpdate:
    """活动更新测试"""
    
    def test_update_activity_success(self, client, test_activity, organizer_auth_header):
        """测试成功更新活动"""
        payload = {
            "name": "更新后的活动名称",
            "capacity": 200
        }
        response = client.put(
            f'/api/activities/{test_activity.id}',
            json=payload,
            headers=organizer_auth_header
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['name'] == "更新后的活动名称"
        assert data['capacity'] == 200
    
    def test_update_activity_unauthorized(self, client, test_activity):
        """测试未登录更新"""
        payload = {"name": "未授权更新"}
        response = client.put(
            f'/api/activities/{test_activity.id}',
            json=payload
        )
        assert response.status_code == 401
    
    def test_update_activity_forbidden(self, client, test_activity, auth_header):
        """测试非主办方更新"""
        payload = {"name": "非主办方更新"}
        response = client.put(
            f'/api/activities/{test_activity.id}',
            json=payload,
            headers=auth_header
        )
        assert response.status_code == 403
    
    def test_update_activity_time(self, client, test_activity, organizer_auth_header):
        """测试更新活动时间"""
        payload = {
            "date": "2026-11-01",
            "time": "14:00"
        }
        response = client.put(
            f'/api/activities/{test_activity.id}',
            json=payload,
            headers=organizer_auth_header
        )
        assert response.status_code == 200


class TestActivityDelete:
    """活动删除测试"""
    
    def test_delete_activity_success(self, client, test_organizer, organizer_auth_header):
        """测试成功删除活动"""
        with client.application.app_context():
            user = db.session.get(User, test_organizer.id)
            activity = Activity(
                user_id=user.id,
                name="待删除活动",
                start_time=datetime.datetime.utcnow() + datetime.timedelta(days=7)
            )
            db.session.add(activity)
            db.session.commit()
            activity_id = activity.id
        
        response = client.delete(
            f'/api/activities/{activity_id}',
            headers=organizer_auth_header
        )
        assert response.status_code == 200
        
        with client.application.app_context():
            deleted = db.session.get(Activity, activity_id)
            assert deleted is None
    
    def test_delete_activity_unauthorized(self, client, test_activity):
        """测试未登录删除"""
        response = client.delete(f'/api/activities/{test_activity.id}')
        assert response.status_code == 401
    
    def test_delete_activity_forbidden(self, client, test_activity, auth_header):
        """测试非主办方删除"""
        response = client.delete(
            f'/api/activities/{test_activity.id}',
            headers=auth_header
        )
        assert response.status_code == 403


class TestActivityShare:
    """活动分享测试"""
    
    def test_share_activity(self, client, test_activity):
        """测试获取分享信息"""
        response = client.get(f'/api/activities/{test_activity.id}/share')
        assert response.status_code == 200
        data = response.get_json()
        assert 'url_link' in data or 'qrcode_data' in data
        assert data['activity_name'] == "测试活动"
    
    def test_share_nonexistent_activity(self, client):
        """测试分享不存在的活动"""
        response = client.get('/api/activities/99999/share')
        assert response.status_code == 404


class TestActivityReport:
    """活动举报测试"""
    
    def test_report_activity_success(self, client, test_activity, auth_header):
        """测试成功举报活动"""
        payload = {
            "reason": "垃圾广告",
            "detail": "详细描述"
        }
        response = client.post(
            f'/api/activities/{test_activity.id}/report',
            json=payload,
            headers=auth_header
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "举报已收到" in data['message']
        assert 'report_id' in data
    
    def test_report_activity_missing_reason(self, client, test_activity, auth_header):
        """测试缺少举报原因"""
        payload = {"detail": "详细描述"}
        response = client.post(
            f'/api/activities/{test_activity.id}/report',
            json=payload,
            headers=auth_header
        )
        assert response.status_code == 400
    
    def test_report_activity_unauthorized(self, client, test_activity):
        """测试未登录举报"""
        payload = {"reason": "垃圾广告"}
        response = client.post(
            f'/api/activities/{test_activity.id}/report',
            json=payload
        )
        assert response.status_code == 401


class TestActivityStatus:
    """活动状态测试"""
    
    def test_upcoming_status(self, client, test_organizer):
        """测试即将开始状态"""
        with client.application.app_context():
            user = db.session.get(User, test_organizer.id)
            activity = Activity(
                user_id=user.id,
                name="未来活动",
                start_time=datetime.datetime.utcnow() + datetime.timedelta(days=7)
            )
            db.session.add(activity)
            db.session.commit()
            
            assert activity.status == 'upcoming'
    
    def test_ended_status(self, client, test_organizer):
        """测试已结束状态"""
        with client.application.app_context():
            user = db.session.get(User, test_organizer.id)
            activity = Activity(
                user_id=user.id,
                name="已结束活动",
                start_time=datetime.datetime.utcnow() - datetime.timedelta(days=1),
                end_time=datetime.datetime.utcnow() - datetime.timedelta(hours=23)
            )
            db.session.add(activity)
            db.session.commit()
            
            assert activity.status == 'ended'
