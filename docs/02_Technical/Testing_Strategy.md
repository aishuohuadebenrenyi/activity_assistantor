# 测试策略文档

> 版本：1.0  
> 更新日期：2026-03-26  
> 适用范围：Zentro 活动助手后端服务

---

## 一、测试策略概述

### 1.1 测试金字塔

```
                    ┌─────────┐
                   │   E2E   │  (端到端测试)
                  ┌┴─────────┴┐
                 │ 集成测试    │  (Integration Tests)
                ┌┴────────────┴┐
               │   单元测试     │  (Unit Tests)
              └─────────────────┘
```

### 1.2 测试覆盖率目标

| 测试类型 | 目标覆盖率 | 当前状态 |
|----------|------------|----------|
| 单元测试 | ≥ 80% | 待测量 |
| 集成测试 | ≥ 60% | 待测量 |
| E2E测试 | 关键流程100% | 待实现 |

---

## 二、测试框架配置

### 2.1 依赖安装

```bash
pip install pytest pytest-flask pytest-cov pytest-mock
```

### 2.2 运行测试

```bash
# 运行所有测试
cd backend
pytest

# 运行指定测试文件
pytest tests/test_activity.py

# 运行指定测试类
pytest tests/test_activity.py::TestActivityCreate

# 运行指定测试方法
pytest tests/test_activity.py::TestActivityCreate::test_create_activity_success

# 运行并生成覆盖率报告
pytest --cov=. --cov-report=html

# 运行慢速测试
pytest -m slow

# 跳过慢速测试
pytest -m "not slow"

# 运行单元测试
pytest -m unit

# 运行集成测试
pytest -m integration
```

### 2.3 pytest.ini 配置

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v 
    --tb=short 
    --strict-markers
    --cov=.
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-report=xml:coverage.xml
    --cov-fail-under=60
```

---

## 三、测试用例编写规范

### 3.1 测试命名规范

```python
# 测试文件命名：test_<module>.py
test_activity.py
test_participant.py
test_auth.py

# 测试类命名：Test<Feature>
class TestActivityCreate:
    pass

# 测试方法命名：test_<action>_<condition>_<expected>
def test_create_activity_success(self):
    pass

def test_create_activity_missing_required(self):
    pass

def test_create_activity_unauthorized(self):
    pass
```

### 3.2 测试结构（AAA模式）

```python
def test_create_activity_success(self, client, organizer_auth_header):
    # Arrange (准备)
    payload = {
        "name": "新创建的活动",
        "date": "2026-10-01",
        "time": "10:00"
    }
    
    # Act (执行)
    response = client.post(
        '/api/activities/',
        json=payload,
        headers=organizer_auth_header
    )
    
    # Assert (断言)
    assert response.status_code == 201
    data = response.get_json()
    assert data['name'] == "新创建的活动"
```

### 3.3 Fixtures 使用

```python
# conftest.py 中定义的 fixtures
@pytest.fixture
def test_user(app):
    """创建测试用户"""
    with app.app_context():
        user = User(phone="13800138000", username="测试用户")
        db.session.add(user)
        db.session.commit()
        return user

@pytest.fixture
def auth_header(app, test_user):
    """生成认证头"""
    with app.app_context():
        user = db.session.get(User, test_user.id)
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        return {'Authorization': f'Bearer {token}'}

# 测试中使用 fixtures
def test_with_fixtures(self, client, test_user, auth_header):
    response = client.get('/api/user/profile', headers=auth_header)
    assert response.status_code == 200
```

---

## 四、测试覆盖范围

### 4.1 活动模块测试

| 测试场景 | 测试用例 | 状态 |
|----------|----------|------|
| 活动列表 | 空列表、分页、搜索 | ✅ |
| 活动创建 | 成功、缺少必填、未授权 | ✅ |
| 活动详情 | 获取详情、不存在、浏览量 | ✅ |
| 活动更新 | 成功、未授权、禁止访问 | ✅ |
| 活动删除 | 成功、未授权、禁止访问 | ✅ |
| 活动分享 | 获取分享信息 | ✅ |
| 活动举报 | 成功、缺少原因、未授权 | ✅ |
| 活动状态 | 即将开始、已结束 | ✅ |

### 4.2 报名模块测试

| 测试场景 | 测试用例 | 状态 |
|----------|----------|------|
| 报名活动 | 成功、重复用户、重复手机号、名额已满 | ✅ |
| 取消报名 | 成功、已签到无法取消 | ✅ |
| 获取票据 | 成功、未报名、票据格式 | ✅ |
| 参与者列表 | 主办方获取、非主办方禁止 | ✅ |
| 签到 | 扫码签到、重复签到、手动签到 | ✅ |
| 签到异常 | 无权限、无效二维码、错误活动 | ✅ |
| 取消签到 | 成功、无权限 | ✅ |

### 4.3 认证模块测试

| 测试场景 | 测试用例 | 状态 |
|----------|----------|------|
| 微信登录 | 成功、无效code | 待实现 |
| Token验证 | 有效、过期、无效 | 待实现 |
| 用户信息 | 获取、更新 | 待实现 |
| 账号注销 | 成功、冷静期 | 待实现 |

---

## 五、Mock 和 Stub

### 5.1 Mock 外部服务

```python
from unittest.mock import patch, MagicMock

class TestWeChatIntegration:
    """微信集成测试"""
    
    @patch('backend.services.wechat_service.WeChatService.get_access_token')
    def test_wechat_login_success(self, mock_get_token, client):
        # Mock 返回值
        mock_get_token.return_value = "mock_access_token"
        
        # 测试逻辑
        response = client.post('/api/auth/wechat-login', json={
            "code": "test_code"
        })
        
        assert response.status_code == 200
    
    @patch('backend.services.wechat_service.WeChatService.check_content_security')
    def test_content_security_check(self, mock_check, client, organizer_auth_header):
        # Mock 内容安全检查返回 True
        mock_check.return_value = True
        
        payload = {
            "name": "测试活动",
            "date": "2026-10-01",
            "time": "10:00"
        }
        response = client.post(
            '/api/activities/',
            json=payload,
            headers=organizer_auth_header
        )
        assert response.status_code == 201
```

### 5.2 Mock 数据库操作

```python
from unittest.mock import patch

class TestDatabaseMock:
    """数据库 Mock 测试"""
    
    @patch('backend.models.User.query')
    def test_get_user_mock(self, mock_query, client):
        # Mock 用户查询
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = "测试用户"
        mock_query.get.return_value = mock_user
        
        # 测试逻辑
        response = client.get('/api/user/1')
        assert response.status_code == 200
```

---

## 六、测试报告

### 6.1 生成覆盖率报告

```bash
# 生成HTML报告
pytest --cov=. --cov-report=html

# 查看报告
open htmlcov/index.html

# 生成XML报告（用于CI）
pytest --cov=. --cov-report=xml

# 上传到Codecov
codecov -f coverage.xml
```

### 6.2 覆盖率报告解读

```
Name                              Stmts   Miss  Cover   Missing
---------------------------------------------------------------
backend/__init__.py                   1      0   100%
backend/app.py                       45      5    89%   23-27
backend/models.py                    80     10    88%   45-50, 78-82
backend/routes/activity.py          150     20    87%   34-38, 156-160
---------------------------------------------------------------
TOTAL                               276     35    87%
```

### 6.3 CI/CD 集成

```yaml
# .github/workflows/ci-cd.yml
- name: Run tests with coverage
  run: |
    cd backend
    pytest tests/ -v --cov=. --cov-report=xml --cov-fail-under=60

- name: Upload coverage report
  uses: codecov/codecov-action@v3
  with:
    files: ./backend/coverage.xml
    flags: unittests
    name: backend-coverage
```

---

## 七、测试最佳实践

### 7.1 测试原则

1. **独立性**：每个测试应该独立运行，不依赖其他测试
2. **可重复性**：测试结果应该可重复
3. **快速性**：测试应该快速执行
4. **清晰性**：测试意图应该清晰明确
5. **完整性**：覆盖正常和异常场景

### 7.2 避免的反模式

```python
# ❌ 不好的做法：测试依赖执行顺序
def test_create_user(self):
    self.user_id = 1  # 依赖其他测试

def test_get_user(self):
    user = get_user(self.user_id)  # 依赖上一个测试

# ✅ 好的做法：每个测试独立
def test_create_user(self, client):
    response = client.post('/api/users', json={...})
    assert response.status_code == 201

def test_get_user(self, client, test_user):
    response = client.get(f'/api/users/{test_user.id}')
    assert response.status_code == 200
```

### 7.3 测试数据管理

```python
# 使用 fixtures 管理测试数据
@pytest.fixture
def sample_activity_data():
    return {
        "name": "测试活动",
        "date": "2026-10-01",
        "time": "10:00",
        "location": "测试地点",
        "capacity": 100
    }

def test_with_sample_data(self, client, sample_activity_data, auth_header):
    response = client.post(
        '/api/activities/',
        json=sample_activity_data,
        headers=auth_header
    )
    assert response.status_code == 201
```

---

## 八、持续改进

### 8.1 定期审查

- 每周审查测试覆盖率报告
- 识别未覆盖的关键代码路径
- 添加缺失的测试用例

### 8.2 测试维护

- 代码重构时同步更新测试
- 删除过时的测试用例
- 优化慢速测试

### 8.3 测试指标

| 指标 | 目标 | 监控频率 |
|------|------|----------|
| 代码覆盖率 | ≥ 80% | 每次提交 |
| 测试通过率 | 100% | 每次提交 |
| 测试执行时间 | < 5分钟 | 每次提交 |
| 缺陷逃逸率 | < 5% | 每月 |

---

## 九、文档变更记录

| 版本 | 日期 | 变更内容 | 变更人 |
|------|------|----------|--------|
| 1.0 | 2026-03-26 | 初始版本 | - |
