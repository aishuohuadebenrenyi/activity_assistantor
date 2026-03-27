"""
统一日志管理模块

提供企业级日志管理能力：
- 统一的日志格式规范（JSON结构化日志）
- 明确的日志级别标准（DEBUG/INFO/WARN/ERROR/FATAL）
- 请求链路追踪（request_id集成）
- 敏感信息自动脱敏
- 日志聚合支持

使用方式：
    from backend.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.info("操作成功", extra={"user_id": 123, "action": "create_activity"})
"""

import os
import sys
import json
import logging
import re
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, Optional

LOG_FORMAT = os.environ.get('LOG_FORMAT', 'json')
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
LOG_INCLUDE_TIMESTAMP = os.environ.get('LOG_INCLUDE_TIMESTAMP', 'true').lower() == 'true'

SENSITIVE_FIELDS = [
    'password', 'passwd', 'pwd', 'secret', 'token', 'api_key', 'apikey',
    'authorization', 'auth', 'credential', 'private_key', 'privatekey',
    'access_token', 'refresh_token', 'session_id', 'cookie',
    'phone', 'mobile', 'email', 'id_card', 'bank_card', 'credit_card',
    'wechat_secret', 'secret_key', 'ssl_key', 'private_key'
]

SENSITIVE_PATTERNS = [
    re.compile(r'(phone|mobile)["\s:=]+(\d{3})\d{4}(\d{4})', re.IGNORECASE),
    re.compile(r'(email)["\s:=]+([a-zA-Z0-9])[a-zA-Z0-9._%+-]*(@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', re.IGNORECASE),
    re.compile(r'(id_card|身份证)["\s:=]+(\d{3})\d{11}(\d{4})', re.IGNORECASE),
    re.compile(r'(bank_card|银行卡|credit_card)["\s:=]+(\d{4})\d+(\d{4})', re.IGNORECASE),
]


class SensitiveDataFilter:
    """敏感数据过滤器"""
    
    @staticmethod
    def mask_value(key: str, value: Any) -> Any:
        """对敏感字段值进行脱敏处理"""
        if not isinstance(value, str):
            return value
        
        key_lower = key.lower()
        for sensitive in SENSITIVE_FIELDS:
            if sensitive in key_lower:
                if len(value) <= 4:
                    return '****'
                return value[:2] + '****' + value[-2:]
        
        return value
    
    @staticmethod
    def mask_string(text: str) -> str:
        """对字符串中的敏感信息进行脱敏"""
        result = text
        for pattern in SENSITIVE_PATTERNS:
            result = pattern.sub(lambda m: f'{m.group(1)}: {m.group(2)}****{m.group(3)}', result)
        return result
    
    @classmethod
    def filter_dict(cls, data: Dict) -> Dict:
        """递归过滤字典中的敏感数据"""
        if not isinstance(data, dict):
            return data
        
        result = {}
        for key, value in data.items():
            if isinstance(value, dict):
                result[key] = cls.filter_dict(value)
            elif isinstance(value, list):
                result[key] = [cls.filter_dict(item) if isinstance(item, dict) else item for item in value]
            else:
                result[key] = cls.mask_value(key, value)
        
        return result


class JsonFormatter(logging.Formatter):
    """JSON格式日志格式化器"""
    
    def __init__(self, include_timestamp: bool = True):
        super().__init__()
        self.include_timestamp = include_timestamp
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为JSON"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        if hasattr(record, 'request_id') and record.request_id:
            log_data['request_id'] = record.request_id
        
        if hasattr(record, 'user_id') and record.user_id:
            log_data['user_id'] = record.user_id
        
        if hasattr(record, 'extra_data') and record.extra_data:
            filtered_extra = SensitiveDataFilter.filter_dict(record.extra_data)
            log_data['data'] = filtered_extra
        
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': self.formatException(record.exc_info)
            }
        
        return json.dumps(log_data, ensure_ascii=False, default=str)


class TextFormatter(logging.Formatter):
    """文本格式日志格式化器（开发环境使用）"""
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为可读文本"""
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        
        parts = [f"[{timestamp}]", f"[{record.levelname:5}]", f"[{record.name}]", record.getMessage()]
        
        if hasattr(record, 'request_id') and record.request_id:
            parts.insert(2, f"[req:{record.request_id[:8]}]")
        
        if hasattr(record, 'user_id') and record.user_id:
            parts.insert(3, f"[user:{record.user_id}]")
        
        result = ' '.join(parts)
        
        if record.exc_info:
            result += '\n' + self.formatException(record.exc_info)
        
        return result


class ContextAdapter(logging.LoggerAdapter):
    """日志上下文适配器，支持添加额外上下文信息"""
    
    def process(self, msg: str, kwargs: Dict) -> tuple:
        """处理日志消息，添加上下文信息"""
        extra = kwargs.get('extra', {})
        
        if self.extra:
            extra.update(self.extra)
        
        kwargs['extra'] = extra
        return msg, kwargs


@lru_cache(maxsize=128)
def get_logger(name: str) -> logging.Logger:
    """
    获取配置好的Logger实例
    
    Args:
        name: 模块名称，通常使用 __name__
    
    Returns:
        配置好的Logger实例
    
    Example:
        logger = get_logger(__name__)
        logger.info("操作成功")
        logger.error("操作失败", extra={"error_code": "E001"})
    """
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
    
    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    logger.propagate = False
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    
    if LOG_FORMAT.lower() == 'json':
        formatter = JsonFormatter(include_timestamp=LOG_INCLUDE_TIMESTAMP)
    else:
        formatter = TextFormatter()
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


def log_with_context(
    logger: logging.Logger,
    level: int,
    message: str,
    request_id: Optional[str] = None,
    user_id: Optional[int] = None,
    **extra_data
) -> None:
    """
    带上下文信息的日志记录
    
    Args:
        logger: Logger实例
        level: 日志级别
        message: 日志消息
        request_id: 请求ID
        user_id: 用户ID
        **extra_data: 额外的上下文数据
    """
    extra = {'extra_data': extra_data}
    
    if request_id:
        extra['request_id'] = request_id
    
    if user_id:
        extra['user_id'] = user_id
    
    logger.log(level, message, extra=extra)


class LogLevel:
    """日志级别常量及使用场景说明"""
    
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL
    
    USAGE_GUIDE = {
        DEBUG: """
        DEBUG (调试级别):
        - 开发调试时的详细信息
        - 变量值、函数调用栈
        - 性能分析数据
        - 仅开发环境使用，生产环境禁用
        """,
        INFO: """
        INFO (信息级别):
        - 正常业务操作记录
        - 用户登录/登出
        - 关键业务节点（创建活动、报名成功等）
        - 定时任务执行状态
        - 外部服务调用成功
        """,
        WARNING: """
        WARNING (警告级别):
        - 潜在问题，但不影响系统运行
        - 接近资源限制（如连接池快满）
        - 降级处理（如缓存不可用，回退到数据库）
        - 业务规则警告（如名额即将满）
        - 重试操作
        """,
        ERROR: """
        ERROR (错误级别):
        - 业务异常（如用户操作失败）
        - 外部服务调用失败
        - 数据校验失败
        - 需要关注的错误，但不影响系统整体运行
        """,
        CRITICAL: """
        CRITICAL (严重级别):
        - 系统级故障
        - 数据库连接失败
        - 核心服务不可用
        - 需要立即处理的严重问题
        - 可能导致系统不可用的错误
        """
    }


def init_app_logging(app) -> None:
    """
    初始化Flask应用的日志配置
    
    Args:
        app: Flask应用实例
    """
    log_level = getattr(logging, LOG_LEVEL, logging.INFO)
    
    app.logger.setLevel(log_level)
    
    for handler in app.logger.handlers[:]:
        app.logger.removeHandler(handler)
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    
    if LOG_FORMAT.lower() == 'json':
        formatter = JsonFormatter()
    else:
        formatter = TextFormatter()
    
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)
    
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.WARNING)
    
    sqlalchemy_logger = logging.getLogger('sqlalchemy.engine')
    if LOG_LEVEL == 'DEBUG':
        sqlalchemy_logger.setLevel(logging.INFO)
    else:
        sqlalchemy_logger.setLevel(logging.WARNING)
    
    get_logger(__name__).info(
        "日志系统初始化完成",
        extra={'extra_data': {
            'log_level': LOG_LEVEL,
            'log_format': LOG_FORMAT
        }}
    )
