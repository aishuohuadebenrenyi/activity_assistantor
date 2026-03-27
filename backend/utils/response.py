"""
统一 API 响应格式工具类。

提供标准化的成功和错误响应格式，确保 API 返回格式一致。
"""

from flask import jsonify
from typing import Any, Optional, Dict


class APIResponse:
    """
    统一 API 响应格式工具类。
    
    使用方式：
    - 成功：return APIResponse.success(data={'id': 1})
    - 错误：return APIResponse.error('操作失败', 'OPERATION_FAILED')
    - 创建：return APIResponse.created(data={'id': 1})
    - 未找到：return APIResponse.not_found('资源不存在')
    """
    
    @staticmethod
    def success(data: Any = None, message: str = 'success', **kwargs):
        """
        成功响应。
        
        参数：
        - data: 响应数据
        - message: 响应消息
        - **kwargs: 其他附加字段
        
        返回：
        - tuple: (response, 200)
        """
        response = {
            'success': True,
            'message': message,
        }
        if data is not None:
            response['data'] = data
        response.update(kwargs)
        return jsonify(response), 200
    
    @staticmethod
    def error(message: str, code: str = 'UNKNOWN_ERROR', status: int = 400, **kwargs):
        """
        错误响应。
        
        参数：
        - message: 错误消息
        - code: 错误代码
        - status: HTTP 状态码
        - **kwargs: 其他附加字段
        
        返回：
        - tuple: (response, status)
        """
        response = {
            'success': False,
            'error': {
                'code': code,
                'message': message,
            }
        }
        if kwargs:
            response['error'].update(kwargs)
        return jsonify(response), status
    
    @staticmethod
    def created(data: Any = None, message: str = 'created'):
        """
        创建成功响应（201）。
        
        参数：
        - data: 响应数据
        - message: 响应消息
        
        返回：
        - tuple: (response, 201)
        """
        return APIResponse.success(data=data, message=message), 201
    
    @staticmethod
    def not_found(message: str = 'Resource not found', code: str = 'NOT_FOUND'):
        """
        资源不存在响应（404）。
        
        参数：
        - message: 错误消息
        - code: 错误代码
        
        返回：
        - tuple: (response, 404)
        """
        return APIResponse.error(message, code, 404)
    
    @staticmethod
    def unauthorized(message: str = 'Unauthorized', code: str = 'UNAUTHORIZED'):
        """
        未授权响应（401）。
        
        参数：
        - message: 错误消息
        - code: 错误代码
        
        返回：
        - tuple: (response, 401)
        """
        return APIResponse.error(message, code, 401)
    
    @staticmethod
    def forbidden(message: str = 'Forbidden', code: str = 'FORBIDDEN'):
        """
        禁止访问响应（403）。
        
        参数：
        - message: 错误消息
        - code: 错误代码
        
        返回:
        - tuple: (response, 403)
        """
        return APIResponse.error(message, code, 403)
    
    @staticmethod
    def bad_request(message: str = 'Bad request', code: str = 'BAD_REQUEST', **kwargs):
        """
        请求参数错误响应（400）。
        
        参数：
        - message: 错误消息
        - code: 错误代码
        - **kwargs: 其他附加字段（如 field, details 等）
        
        返回：
        - tuple: (response, 400)
        """
        return APIResponse.error(message, code, 400, **kwargs)
    
    @staticmethod
    def server_error(message: str = 'Internal server error', code: str = 'INTERNAL_ERROR'):
        """
        服务器内部错误响应（500）。
        
        参数：
        - message: 错误消息
        - code: 错误代码
        
        返回：
        - tuple: (response, 500)
        """
        return APIResponse.error(message, code, 500)
    
    @staticmethod
    def accepted(message: str = 'Request accepted', data: Any = None):
        """
        请求已接受响应（202）。
        
        用于异步处理场景，如导出、批量操作等。
        
        参数：
        - message: 响应消息
        - data: 响应数据
        
        返回：
        - tuple: (response, 202)
        """
        return APIResponse.success(data=data, message=message), 202


class AppException(Exception):
    """
    应用基础异常类。
    
    使用方式：
    - raise ValidationError('参数错误', field='name')
    - raise NotFoundError('活动不存在')
    - raise ForbiddenError('没有权限')
    """
    
    def __init__(self, message: str, code: str = 'APP_ERROR', status: int = 400):
        self.message = message
        self.code = code
        self.status = status
        super().__init__(message)


class ValidationError(AppException):
    """校验错误异常。"""
    
    def __init__(self, message: str, field: str = None, code: str = 'VALIDATION_ERROR'):
        self.field = field
        super().__init__(message, code, 400)


class NotFoundError(AppException):
    """资源不存在异常。"""
    
    def __init__(self, resource: str = 'Resource', code: str = 'NOT_FOUND'):
        super().__init__(f'{resource}不存在', code, 404)


class ForbiddenError(AppException):
    """禁止访问异常。"""
    
    def __init__(self, message: str = '没有权限访问', code: str = 'FORBIDDEN'):
        super().__init__(message, code, 403)


class UnauthorizedError(AppException):
    """未授权异常。"""
    
    def __init__(self, message: str = '未授权访问', code: str = 'UNAUTHORIZED'):
        super().__init__(message, code, 401)


class BusinessError(AppException):
    """业务逻辑错误异常。"""
    
    def __init__(self, message: str, code: str = 'BUSINESS_ERROR'):
        super().__init__(message, code, 400)
