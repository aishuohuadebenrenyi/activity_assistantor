"""
OpenAPI/Swagger 文档配置模块

提供企业级API文档能力：
- 自动生成Swagger UI
- 统一的API文档模板
- 版本控制支持
- 认证配置

访问地址：
- Swagger UI: /apidocs
- API JSON: /apispec_1.json
"""

import os
from typing import Dict, List, Any

SWAGGER_CONFIG = {
    'headers': [],
    'specs': [
        {
            'endpoint': 'apispec',
            'route': '/apispec.json',
            'rule_filter': lambda rule: True,
            'model_filter': lambda tag: True,
        }
    ],
    'static_url_path': '/flasgger_static',
    'swagger_ui': True,
    'specs_route': '/apidocs'
}

SWAGGER_TEMPLATE = {
    'openapi': '3.0.3',
    'info': {
        'title': 'Zentro 活动助手 API',
        'description': """
## 概述

Zentro 活动助手是一个活动管理平台，支持主办方创建和管理活动，参与者报名和签到。

## 平台说明

- **App端 (iOS/Android)**: 主办方使用，用于活动创建、编辑、签到管理
- **小程序端 (微信)**: 参与者使用，用于活动浏览、报名、查看票据

## 认证方式

API使用 JWT Bearer Token 认证：
```
Authorization: Bearer <your_jwt_token>
```

## 幂等性控制

所有写操作（POST/PUT/DELETE）需要携带 `Idempotency-Key` 请求头：
```
Idempotency-Key: <client-generated-uuid>
```

## 错误码说明

| 错误码 | 说明 |
|--------|------|
| AUTH_UNAUTHORIZED | 未登录或Token过期 |
| AUTH_FORBIDDEN | 无权限访问 |
| REQ_INVALID | 请求参数无效 |
| NOT_FOUND | 资源不存在 |
| CONFLICT | 资源冲突 |
| RATE_LIMITED | 请求频率超限 |
| INTERNAL_ERROR | 服务器内部错误 |
        """,
        'contact': {
            'name': 'Zentro 技术支持',
            'email': 'support@zentro.app'
        },
        'version': '1.0.0',
        'license': {
            'name': 'MIT',
            'url': 'https://opensource.org/licenses/MIT'
        }
    },
    'components': {
        'securitySchemes': {
            'Bearer': {
                'type': 'http',
                'scheme': 'bearer',
                'bearerFormat': 'JWT',
                'description': 'JWT Token 认证，格式: Bearer <token>'
            }
        },
        'schemas': {
            'ErrorResponse': {
                'type': 'object',
                'properties': {
                    'code': {
                        'type': 'string',
                        'description': '错误码',
                        'example': 'REQ_INVALID'
                    },
                    'message': {
                        'type': 'string',
                        'description': '错误信息',
                        'example': '请求参数无效'
                    }
                }
            },
            'Activity': {
                'type': 'object',
                'properties': {
                    'id': {
                        'type': 'integer',
                        'description': '活动ID',
                        'example': 1
                    },
                    'organizer_id': {
                        'type': 'integer',
                        'description': '主办方用户ID',
                        'example': 1
                    },
                    'name': {
                        'type': 'string',
                        'description': '活动名称',
                        'example': '2024年度技术分享会'
                    },
                    'type': {
                        'type': 'string',
                        'description': '活动类型',
                        'example': 'business'
                    },
                    'start_time': {
                        'type': 'string',
                        'format': 'date-time',
                        'description': '开始时间',
                        'example': '2024-03-25T14:00:00'
                    },
                    'end_time': {
                        'type': 'string',
                        'format': 'date-time',
                        'description': '结束时间',
                        'example': '2024-03-25T16:00:00'
                    },
                    'location': {
                        'type': 'string',
                        'description': '活动地点',
                        'example': '北京市朝阳区xxx大厦'
                    },
                    'description': {
                        'type': 'string',
                        'description': '活动介绍',
                        'example': '本次分享会将探讨最新技术趋势...'
                    },
                    'capacity': {
                        'type': 'integer',
                        'description': '人数限制，0表示不限',
                        'example': 100
                    },
                    'views_count': {
                        'type': 'integer',
                        'description': '浏览量',
                        'example': 128
                    },
                    'status': {
                        'type': 'string',
                        'description': '活动状态',
                        'enum': ['upcoming', 'ongoing', 'ended'],
                        'example': 'upcoming'
                    },
                    'host_phone': {
                        'type': 'string',
                        'description': '主办方电话（脱敏）',
                        'example': '138****8000'
                    },
                    'host_wechat': {
                        'type': 'string',
                        'description': '主办方微信（脱敏）',
                        'example': 'wch****id'
                    },
                    'show_phone': {
                        'type': 'boolean',
                        'description': '是否显示电话'
                    },
                    'show_wechat': {
                        'type': 'boolean',
                        'description': '是否显示微信'
                    },
                    'created_at': {
                        'type': 'string',
                        'format': 'date-time',
                        'description': '创建时间'
                    }
                }
            },
            'Registration': {
                'type': 'object',
                'properties': {
                    'id': {
                        'type': 'integer',
                        'description': '报名记录ID',
                        'example': 1
                    },
                    'activity_id': {
                        'type': 'integer',
                        'description': '活动ID'
                    },
                    'user_id': {
                        'type': 'integer',
                        'description': '用户ID'
                    },
                    'name': {
                        'type': 'string',
                        'description': '报名人姓名',
                        'example': '张三'
                    },
                    'phone': {
                        'type': 'string',
                        'description': '手机号（脱敏）',
                        'example': '138****5678'
                    },
                    'created_at': {
                        'type': 'string',
                        'format': 'date-time',
                        'description': '报名时间'
                    },
                    'checked_in': {
                        'type': 'boolean',
                        'description': '是否已签到'
                    },
                    'checkin_time': {
                        'type': 'string',
                        'format': 'date-time',
                        'description': '签到时间'
                    }
                }
            },
            'User': {
                'type': 'object',
                'properties': {
                    'id': {
                        'type': 'integer',
                        'description': '用户ID',
                        'example': 1
                    },
                    'username': {
                        'type': 'string',
                        'description': '用户名',
                        'example': '张三'
                    },
                    'phone': {
                        'type': 'string',
                        'description': '手机号（脱敏）',
                        'example': '138****5678'
                    },
                    'avatar_url': {
                        'type': 'string',
                        'description': '头像URL'
                    },
                    'created_at': {
                        'type': 'string',
                        'format': 'date-time',
                        'description': '注册时间'
                    }
                }
            },
            'CheckinRecord': {
                'type': 'object',
                'properties': {
                    'id': {
                        'type': 'integer',
                        'description': '签到记录ID'
                    },
                    'registration_id': {
                        'type': 'integer',
                        'description': '报名记录ID'
                    },
                    'activity_id': {
                        'type': 'integer',
                        'description': '活动ID'
                    },
                    'checkin_time': {
                        'type': 'string',
                        'format': 'date-time',
                        'description': '签到时间'
                    }
                }
            }
        },
        'responses': {
            'UnauthorizedError': {
                'description': '未授权 - Token无效或已过期',
                'content': {
                    'application/json': {
                        'schema': {
                            '$ref': '#/components/schemas/ErrorResponse'
                        },
                        'example': {
                            'code': 'AUTH_UNAUTHORIZED',
                            'message': '请先登录'
                        }
                    }
                }
            },
            'ForbiddenError': {
                'description': '禁止访问 - 无权限',
                'content': {
                    'application/json': {
                        'schema': {
                            '$ref': '#/components/schemas/ErrorResponse'
                        },
                        'example': {
                            'code': 'AUTH_FORBIDDEN',
                            'message': '无权限访问此资源'
                        }
                    }
                }
            },
            'NotFoundError': {
                'description': '资源不存在',
                'content': {
                    'application/json': {
                        'schema': {
                            '$ref': '#/components/schemas/ErrorResponse'
                        },
                        'example': {
                            'code': 'NOT_FOUND',
                            'message': '请求的资源不存在'
                        }
                    }
                }
            },
            'ValidationError': {
                'description': '请求参数验证失败',
                'content': {
                    'application/json': {
                        'schema': {
                            '$ref': '#/components/schemas/ErrorResponse'
                        },
                        'example': {
                            'code': 'REQ_INVALID',
                            'message': '参数验证失败'
                        }
                    }
                }
            },
            'RateLimitError': {
                'description': '请求频率超限',
                'content': {
                    'application/json': {
                        'schema': {
                            '$ref': '#/components/schemas/ErrorResponse'
                        },
                        'example': {
                            'code': 'RATE_LIMITED',
                            'message': '请求过于频繁，请稍后再试'
                        }
                    }
                }
            }
        },
        'parameters': {
            'ActivityId': {
                'name': 'id',
                'in': 'path',
                'description': '活动ID',
                'required': True,
                'schema': {
                    'type': 'integer'
                }
            },
            'Page': {
                'name': 'page',
                'in': 'query',
                'description': '页码',
                'schema': {
                    'type': 'integer',
                    'default': 1
                }
            },
            'PerPage': {
                'name': 'per_page',
                'in': 'query',
                'description': '每页数量',
                'schema': {
                    'type': 'integer',
                    'default': 20
                }
            }
        }
    },
    'tags': [
        {
            'name': '认证',
            'description': '用户登录、注册、Token管理'
        },
        {
            'name': '活动',
            'description': '活动创建、查询、编辑、删除'
        },
        {
            'name': '报名',
            'description': '活动报名、取消报名、票据'
        },
        {
            'name': '签到',
            'description': '签到操作、签到管理'
        },
        {
            'name': '用户',
            'description': '用户信息、我的活动'
        },
        {
            'name': '分享',
            'description': '活动分享、二维码生成'
        }
    ]
}


def get_swagger_config() -> Dict[str, Any]:
    """获取Swagger配置"""
    return SWAGGER_CONFIG


def get_swagger_template() -> Dict[str, Any]:
    """获取Swagger模板"""
    return SWAGGER_TEMPLATE


def init_swagger(app) -> None:
    """
    初始化Swagger文档
    
    Args:
        app: Flask应用实例
    """
    from flasgger import Swagger
    
    Swagger(app, config=SWAGGER_CONFIG, template=SWAGGER_TEMPLATE)
