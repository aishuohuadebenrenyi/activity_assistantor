"""
报名模块完整测试套件

测试覆盖：
- 报名活动（校验、重复报名）
- 取消报名（条件校验）
- 获取票据
- 参与者列表
- 数据导出
"""

import pytest
import json
import datetime
import base64
from backend.models import db, User, Activity, Registration, CheckinRecord


class TestRegistration:
    """报名测试"""
    
    def test_register_success(self, client, test_activity, auth_header):
        """测试成功报名"""
        payload = {
            "name": "报名用户",
            "phone": "13800138001"
        }
        response = client.post(
            f'/api/activities/{test_activity.id}/register',
            json=payload,
            headers=auth_header
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data['name'] == "报名用户"
        assert data['checked_in'] is False
    
    def test_register_duplicate_user(self, client, test_activity, test_registration, auth_header):
        """测试重复报名（同一用户）"""
        payload = {
            "name": "重复报名",
            "phone": "13800138002"
        }
        response = client.post(
            f'/api/activities/{test_activity.id}/register',
            json=payload,
            headers=auth_header
        )
        assert response.status_code == 400
    
    def test_register_duplicate_phone(self, client, test_activity, test_organizer):
        """测试重复报名（同一手机号）"""
        import jwt
        from flask import current_app
        
        with client.application.app_context():
            user = User(phone="13900139001", username="新用户")
            db.session.add(user)
            db.session.commit()
            user_id = user.id
            
            token = jwt.encode({
                'user_id': user_id,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
            }, client.application.config['SECRET_KEY'], algorithm='HS256')
        
        headers = {'Authorization': f'Bearer {token}'}
        payload = {
            "name": "重复手机号",
            "phone": "13800138000"
        }
        response = client.post(
            f'/api/activities/{test_activity.id}/register',
            json=payload,
            headers=headers
        )
        assert response.status_code == 400
    
    def test_register_capacity_full(self, client, test_organizer):
        """测试名额已满"""
        with client.application.app_context():
            user = db.session.get(User, test_organizer.id)
            activity = Activity(
                user_id=user.id,
                name="名额已满活动",
                start_time=datetime.datetime.utcnow() + datetime.timedelta(days=7),
                capacity=1
            )
            db.session.add(activity)
            db.session.commit()
            
            reg = Registration(
                activity_id=activity.id,
                user_id=user.id,
                name="已报名用户",
                phone="13800138000"
            )
            db.session.add(reg)
            db.session.commit()
            activity_id = activity.id
        
        import jwt
        new_user = User(phone="13900139002", username="新用户")
        db.session.add(new_user)
        db.session.commit()
        
        token = jwt.encode({
            'user_id': new_user.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
        }, client.application.config['SECRET_KEY'], algorithm='HS256')
        
        headers = {'Authorization': f'Bearer {token}'}
        payload = {"name": "新报名", "phone": "13900139002"}
        response = client.post(
            f'/api/activities/{activity_id}/register',
            json=payload,
            headers=headers
        )
        assert response.status_code == 400
    
    def test_register_unauthorized(self, client, test_activity):
        """测试未登录报名"""
        payload = {"name": "未授权报名", "phone": "13800138000"}
        response = client.post(
            f'/api/activities/{test_activity.id}/register',
            json=payload
        )
        assert response.status_code == 401


class TestCancelRegistration:
    """取消报名测试"""
    
    def test_cancel_registration_success(self, client, test_activity, test_user):
        """测试成功取消报名"""
        import jwt
        
        with client.application.app_context():
            user = db.session.get(User, test_user.id)
            activity = db.session.get(Activity, test_activity.id)
            
            reg = Registration(
                activity_id=activity.id,
                user_id=user.id,
                name="待取消报名",
                phone="13800138000"
            )
            db.session.add(reg)
            db.session.commit()
            reg_id = reg.id
            
            token = jwt.encode({
                'user_id': user.id,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
            }, client.application.config['SECRET_KEY'], algorithm='HS256')
        
        headers = {'Authorization': f'Bearer {token}'}
        response = client.delete(
            f'/api/activities/{test_activity.id}/registration',
            headers=headers
        )
        assert response.status_code == 200
    
    def test_cancel_registration_after_checkin(self, client, test_activity, test_user):
        """测试已签到无法取消"""
        import jwt
        
        with client.application.app_context():
            user = db.session.get(User, test_user.id)
            activity = db.session.get(Activity, test_activity.id)
            
            reg = Registration(
                activity_id=activity.id,
                user_id=user.id,
                name="已签到报名",
                phone="13800138000"
            )
            db.session.add(reg)
            db.session.commit()
            
            checkin = CheckinRecord(
                registration_id=reg.id,
                activity_id=activity.id,
                checkin_time=datetime.datetime.utcnow()
            )
            db.session.add(checkin)
            db.session.commit()
            
            token = jwt.encode({
                'user_id': user.id,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
            }, client.application.config['SECRET_KEY'], algorithm='HS256')
        
        headers = {'Authorization': f'Bearer {token}'}
        response = client.delete(
            f'/api/activities/{test_activity.id}/registration',
            headers=headers
        )
        assert response.status_code == 400


class TestTicket:
    """票据测试"""
    
    def test_get_ticket_success(self, client, test_activity, test_registration, auth_header):
        """测试获取票据"""
        response = client.get(
            f'/api/activities/{test_activity.id}/my-ticket',
            headers=auth_header
        )
        assert response.status_code == 200
        data = response.get_json()
        assert 'registration' in data
        assert 'ticket_code' in data
        assert 'qr_code_image' in data
    
    def test_get_ticket_not_registered(self, client, test_activity, auth_header):
        """测试未报名获取票据"""
        with client.application.app_context():
            Registration.query.filter_by(activity_id=test_activity.id).delete()
            db.session.commit()
        
        response = client.get(
            f'/api/activities/{test_activity.id}/my-ticket',
            headers=auth_header
        )
        assert response.status_code == 404
    
    def test_ticket_code_format(self, client, test_activity, test_registration, auth_header):
        """测试票据码格式"""
        response = client.get(
            f'/api/activities/{test_activity.id}/my-ticket',
            headers=auth_header
        )
        assert response.status_code == 200
        data = response.get_json()
        
        ticket_code = data['ticket_code']
        decoded = base64.b64decode(ticket_code).decode('utf-8')
        parts = decoded.split(':')
        
        assert parts[0] == 'CHECKIN'
        assert int(parts[1]) == test_activity.id


class TestParticipants:
    """参与者列表测试"""
    
    def test_get_participants_as_organizer(self, client, test_activity, test_registration, organizer_auth_header):
        """测试主办方获取参与者列表"""
        response = client.get(
            f'/api/activities/{test_activity.id}/participants',
            headers=organizer_auth_header
        )
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
    
    def test_get_participants_forbidden(self, client, test_activity, auth_header):
        """测试非主办方无权限"""
        response = client.get(
            f'/api/activities/{test_activity.id}/participants',
            headers=auth_header
        )
        assert response.status_code == 403


class TestCheckin:
    """签到测试"""
    
    def test_checkin_with_qrcode(self, client, test_activity, test_registration, organizer_auth_header):
        """测试扫码签到"""
        with client.application.app_context():
            reg = db.session.get(Registration, test_registration.id)
            import time
            timestamp = int(time.time())
            
            ticket_code = f"CHECKIN:{test_activity.id}:{reg.id}:{timestamp}"
            qr_data = base64.b64encode(ticket_code.encode()).decode()
        
        payload = {"qr_data": qr_data}
        response = client.post(
            f'/api/activities/{test_activity.id}/checkin',
            json=payload,
            headers=organizer_auth_header
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['already_checked'] is False
    
    def test_checkin_already_checked(self, client, test_activity, test_registration, test_checkin_record, organizer_auth_header):
        """测试重复签到"""
        with client.application.app_context():
            reg = db.session.get(Registration, test_registration.id)
            import time
            timestamp = int(time.time())
            
            ticket_code = f"CHECKIN:{test_activity.id}:{reg.id}:{timestamp}"
            qr_data = base64.b64encode(ticket_code.encode()).decode()
        
        payload = {"qr_data": qr_data}
        response = client.post(
            f'/api/activities/{test_activity.id}/checkin',
            json=payload,
            headers=organizer_auth_header
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['already_checked'] is True
    
    def test_checkin_manual(self, client, test_activity, test_registration, organizer_auth_header):
        """测试手动签到"""
        with client.application.app_context():
            CheckinRecord.query.filter_by(registration_id=test_registration.id).delete()
            db.session.commit()
            reg_id = test_registration.id
        
        payload = {"registration_id": reg_id}
        response = client.post(
            f'/api/activities/{test_activity.id}/checkin',
            json=payload,
            headers=organizer_auth_header
        )
        assert response.status_code == 200
    
    def test_checkin_forbidden(self, client, test_activity, auth_header):
        """测试非主办方签到"""
        payload = {"registration_id": 1}
        response = client.post(
            f'/api/activities/{test_activity.id}/checkin',
            json=payload,
            headers=auth_header
        )
        assert response.status_code == 403
    
    def test_checkin_invalid_qrcode(self, client, test_activity, organizer_auth_header):
        """测试无效二维码"""
        payload = {"qr_data": "invalid_qr_data"}
        response = client.post(
            f'/api/activities/{test_activity.id}/checkin',
            json=payload,
            headers=organizer_auth_header
        )
        assert response.status_code == 400
    
    def test_checkin_wrong_activity(self, client, test_organizer, organizer_auth_header):
        """测试错误活动的签到码"""
        with client.application.app_context():
            user = db.session.get(User, test_organizer.id)
            
            activity1 = Activity(
                user_id=user.id,
                name="活动1",
                start_time=datetime.datetime.utcnow() + datetime.timedelta(days=7)
            )
            activity2 = Activity(
                user_id=user.id,
                name="活动2",
                start_time=datetime.datetime.utcnow() + datetime.timedelta(days=7)
            )
            db.session.add_all([activity1, activity2])
            db.session.commit()
            
            reg = Registration(
                activity_id=activity1.id,
                user_id=user.id,
                name="报名用户",
                phone="13800138000"
            )
            db.session.add(reg)
            db.session.commit()
            
            import time
            timestamp = int(time.time())
            ticket_code = f"CHECKIN:{activity1.id}:{reg.id}:{timestamp}"
            qr_data = base64.b64encode(ticket_code.encode()).decode()
        
        payload = {"qr_data": qr_data}
        response = client.post(
            f'/api/activities/{activity2.id}/checkin',
            json=payload,
            headers=organizer_auth_header
        )
        assert response.status_code == 400


class TestCancelCheckin:
    """取消签到测试"""
    
    def test_cancel_checkin_success(self, client, test_activity, test_registration, test_checkin_record, organizer_auth_header):
        """测试成功取消签到"""
        with client.application.app_context():
            reg_id = test_registration.id
        
        response = client.delete(
            f'/api/activities/{test_activity.id}/checkin/{reg_id}',
            headers=organizer_auth_header
        )
        assert response.status_code == 200
    
    def test_cancel_checkin_forbidden(self, client, test_activity, test_registration, auth_header):
        """测试非主办方取消签到"""
        response = client.delete(
            f'/api/activities/{test_activity.id}/checkin/{test_registration.id}',
            headers=auth_header
        )
        assert response.status_code == 403
