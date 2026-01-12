"""
配置文件 - 电力巡检系统
包含数据库、C++服务、七牛云OSS等配置
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

# 确保在读取任何配置前先加载 .env
load_dotenv()

# 项目根目录
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    """基础配置类"""
    
    # Flask 基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # 数据库配置 (MySQL)
    # 格式: mysql+pymysql://用户名:密码@主机:端口/数据库名
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://root:20221634@127.0.0.1:3306/electric_inspection'

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # 设为 True 可以看到SQL语句
    
    # JWT 配置
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)  # Token 有效期24小时
    
    # 文件上传配置
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'temp_uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 最大上传16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp'}
    
    # C++ 推理服务配置
    CPP_SERVICE_URL = os.environ.get('CPP_SERVICE_URL') or 'http://localhost:8080'
    CPP_PREDICT_ENDPOINT = '/predict'
    CPP_HEALTH_ENDPOINT = '/health'
    CPP_TIMEOUT = 30  # 请求超时时间(秒)
    
    # 七牛云 OSS 配置
    QINIU_ACCESS_KEY = os.environ.get('QINIU_AK') or 'aNVoZjY2OlSWiHIG506cKGzRMPdFQmJ6choNFKFu'
    QINIU_SECRET_KEY = os.environ.get('QINIU_SK') or '8D8h2RXIV6Y9vJXjdlPoLcTJMBmeitKFBKfIELb4'
    QINIU_BUCKET_NAME = os.environ.get('QINIU_BUCKET') or 'electric-inspection'
    QINIU_DOMAIN = os.environ.get('QINIU_DOMAIN') or 'http://cdn.your-domain.com'
    
    # 推理配置
    DEFAULT_CONFIDENCE_THRESHOLD = 0.25
    DEFAULT_MODEL_TYPE = 'v11-m'
    
    # 类别标签映射 (根据你的模型调整)
    CLASS_LABELS = {
        0: 'insulator_broken',
        1: 'insulator_burn',
        2: 'nest',
        3: 'ring_shifted',
        4: 'insulator',
        # 根据实际模型添加更多类别
    }
    
    @staticmethod
    def init_app(app):
        """初始化应用配置"""
        # 确保上传目录存在
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    # 生产环境应该使用环境变量设置密钥
    

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
