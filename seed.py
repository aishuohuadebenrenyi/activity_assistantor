from backend.app import app
from backend.models import db, User, Activity, Registration, CheckinRecord
from datetime import datetime, timedelta
import random

def seed_data():
    with app.app_context():
        print("正在清理数据库...")
        db.drop_all()
        db.create_all()

        print("正在创建用户...")
        organizer = User(
            phone="13800138000",
            username="活动助手管理员",
            bio="致力于打造最优质的活动体验",
            is_certified=True
        )
        db.session.add(organizer)
        db.session.commit()

        print("正在创建活动...")
        # 1. 进行中活动 (Ongoing)
        ongoing_activity = Activity(
            user_id=organizer.id,
            name="2023秋季产品发布会",
            type="meeting",
            start_time=datetime.now() - timedelta(hours=1), # 1小时前开始
            location="北京国际会议中心 Hall A",
            description="年度重磅产品发布，届时将展示最新的AI技术成果，欢迎各位莅临指导。",
            capacity=200,
            status="ongoing",
            views_count=1205
        )

        # 2. 即将开始活动 (Upcoming)
        upcoming_activity = Activity(
            user_id=organizer.id,
            name="企业数字化转型培训",
            type="training",
            start_time=datetime.now() + timedelta(days=3, hours=10),
            location="上海科技园 3号楼培训室",
            description="深入解析传统企业如何进行数字化转型，邀请行业专家授课，干货满满。",
            capacity=50,
            status="upcoming",
            views_count=342
        )

        # 3. 已结束活动 (Ended)
        ended_activity = Activity(
            user_id=organizer.id,
            name="周末户外徒步",
            type="social",
            start_time=datetime.now() - timedelta(days=7),
            location="香山公园",
            description="放松心情，亲近自然，增强团队凝聚力。请自备饮用水和运动装备。",
            capacity=30,
            status="ended",
            views_count=890
        )
        
        db.session.add_all([ongoing_activity, upcoming_activity, ended_activity])
        db.session.commit()

        print("正在生成报名和签到数据...")
        
        first_names = ["张", "李", "王", "赵", "陈", "刘", "杨", "黄", "周", "吴", "郑", "孙"]
        last_names = ["伟", "芳", "娜", "敏", "静", "秀英", "丽", "强", "磊", "洋", "勇", "军", "杰", "娟", "艳", "明", "超"]
        
        def generate_phone():
            prefixes = ["138", "139", "136", "137", "135", "150", "151", "152", "186", "189"]
            prefix = random.choice(prefixes)
            suffix = ''.join([str(random.randint(0, 9)) for _ in range(8)])
            return f"{prefix}{suffix}"

        def generate_name():
            return random.choice(first_names) + random.choice(last_names)

        # 为"进行中"活动生成报名和签到
        # 45人报名，部分已签到
        for _ in range(45):
            reg = Registration(
                activity_id=ongoing_activity.id,
                name=generate_name(),
                phone=generate_phone()
            )
            db.session.add(reg)
            db.session.flush() # 获取ID
            
            # 70% 签到率
            if random.random() < 0.7: 
                checkin = CheckinRecord(
                    registration_id=reg.id,
                    activity_id=ongoing_activity.id,
                    checkin_time=datetime.now() - timedelta(minutes=random.randint(0, 60)),
                    device_info="iPhone 14 Pro" if random.random() > 0.5 else "Huawei Mate 60"
                )
                db.session.add(checkin)

        # 为"即将开始"活动生成报名
        # 12人报名，无签到
        for _ in range(12):
            reg = Registration(
                activity_id=upcoming_activity.id,
                name=generate_name(),
                phone=generate_phone()
            )
            db.session.add(reg)

        # 为"已结束"活动生成报名和签到
        # 28人报名，大部分已签到
        for _ in range(28):
            reg = Registration(
                activity_id=ended_activity.id,
                name=generate_name(),
                phone=generate_phone()
            )
            db.session.add(reg)
            db.session.flush()
            
            # 90% 签到率
            if random.random() < 0.9: 
                checkin = CheckinRecord(
                    registration_id=reg.id,
                    activity_id=ended_activity.id,
                    checkin_time=ended_activity.start_time + timedelta(minutes=random.randint(0, 30)),
                    device_info="Android Device"
                )
                db.session.add(checkin)

        db.session.commit()
        print("数据库假数据生成完毕！")
        print(f"管理员账号: 13800138000")
        print(f"生成的活动ID: {ongoing_activity.id} (进行中), {upcoming_activity.id} (即将开始), {ended_activity.id} (已结束)")

if __name__ == '__main__':
    seed_data()
