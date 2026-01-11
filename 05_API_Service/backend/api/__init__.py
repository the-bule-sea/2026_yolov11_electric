"""API路由模块"""
from flask import Blueprint

# 创建蓝图
auth_bp = Blueprint('auth', __name__)
detect_bp = Blueprint('detect', __name__)
records_bp = Blueprint('records', __name__)
stats_bp = Blueprint('stats', __name__)
