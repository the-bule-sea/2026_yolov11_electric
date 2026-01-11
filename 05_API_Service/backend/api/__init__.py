"""API路由模块"""
from flask import Blueprint

# 创建蓝图
auth_bp = Blueprint('auth', __name__)
detect_bp = Blueprint('detect', __name__)
records_bp = Blueprint('records', __name__)
stats_bp = Blueprint('stats', __name__)

# 必须在蓝图创建之后导入视图模块，否则路由不会注册
# 注意避免循环导入，所以放在最后
from api import auth
from api import detect
from api import records
from api import stats
