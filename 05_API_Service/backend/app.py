"""
Flask应用主入口
电力巡检系统后端服务
"""
from flask import Flask, jsonify
from flask_cors import CORS
from config import config
from models import db
from models.user import create_default_user
from utils.cpp_client import init_cpp_client
from utils.oss_client import init_oss_client
from utils.image_proc import init_image_processor
import os


def create_app(config_name='default'):
    """
    创建Flask应用工厂函数
    
    Args:
        config_name: 配置名称 ('development', 'production', 'testing')
        
    Returns:
        Flask应用实例
    """
    app = Flask(__name__)
    
    # 加载配置
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # 初始化CORS（跨域支持）
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",  # 生产环境应指定具体域名
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # 初始化数据库
    db.init_app(app)
    
    # 创建数据库表和默认用户
    with app.app_context():
        db.create_all()
        create_default_user()
    
    # 初始化工具类客户端
    init_cpp_client(
        app.config['CPP_SERVICE_URL'],
        app.config['CPP_TIMEOUT']
    )
    
    init_oss_client(
        app.config['QINIU_ACCESS_KEY'],
        app.config['QINIU_SECRET_KEY'],
        app.config['QINIU_BUCKET_NAME'],
        app.config['QINIU_DOMAIN']
    )
    
    init_image_processor(app.config['CLASS_LABELS'])
    
    # 注册蓝图
    from api import auth_bp, detect_bp, records_bp, stats_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(detect_bp, url_prefix='/api/v1/detect')
    app.register_blueprint(records_bp, url_prefix='/api/v1/records')
    app.register_blueprint(stats_bp, url_prefix='/api/v1/stats')
    
    # 根路由 - API信息
    @app.route('/')
    def index():
        return jsonify({
            'name': '电力巡检系统 API',
            'version': '2.1',
            'status': 'running',
            'endpoints': {
                'auth': '/api/v1/auth',
                'detect': '/api/v1/detect',
                'records': '/api/v1/records',
                'stats': '/api/v1/stats'
            }
        })
    
    # 健康检查
    @app.route('/health')
    def health():
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': db.func.now()
        })
    
    # 全局错误处理
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'code': 404,
            'msg': '接口不存在'
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': '服务器内部错误'
        }), 500
    
    print("=" * 60)
    print("🚀 电力巡检系统后端服务已启动")
    print("=" * 60)
    print(f"📌 运行环境: {config_name}")
    print(f"📌 数据库: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print(f"📌 C++服务: {app.config['CPP_SERVICE_URL']}")
    print(f"📌 OSS存储: {app.config['QINIU_DOMAIN']}")
    print(f"📌 上传目录: {app.config['UPLOAD_FOLDER']}")
    print("=" * 60)
    
    return app


if __name__ == '__main__':
    # 从环境变量获取配置名称
    env = os.environ.get('FLASK_ENV', 'development')
    
    # 创建应用
    app = create_app(env)
    
    # 运行服务
    app.run(
        host='0.0.0.0',  # 允许外部访问
        port=5000,
        debug=(env == 'development')
    )
