import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-prod'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Aliyun FC specific config can be added here
    FC_SERVICE_NAME = os.environ.get('FC_SERVICE_NAME')

    # WeChat Mini Program Config
    WECHAT_APPID = os.environ.get('WECHAT_APPID') or 'wx1234567890abcdef'
    WECHAT_SECRET = os.environ.get('WECHAT_SECRET') or 'wx1234567890abcdef1234567890abcdef'
