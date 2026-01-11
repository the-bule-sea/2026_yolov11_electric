"""
认证模块 API
提供用户登录、JWT Token发放等功能
"""
from flask import request, jsonify
from api import auth_bp
from models import db
from models.user import User
import jwt
from datetime import datetime, timedelta
from functools import wraps
from config import Config


def create_token(user_id: int, username: str, role: str) -> str:
    """
    创建JWT Token
    
    Args:
        user_id: 用户ID
        username: 用户名
        role: 角色
        
    Returns:
        JWT Token字符串
    """
    payload = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'exp': datetime.utcnow() + Config.JWT_ACCESS_TOKEN_EXPIRES,
        'iat': datetime.utcnow()
    }
    
    token = jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm='HS256')
    return token


def token_required(f):
    """
    JWT Token验证装饰器
    使用方法: @token_required
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # 从Header中获取Token
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]  # 格式: "Bearer <token>"
            except IndexError:
                return jsonify({
                    'code': 401,
                    'msg': 'Token格式错误'
                }), 401
        
        if not token:
            return jsonify({
                'code': 401,
                'msg': '缺少Token'
            }), 401
        
        try:
            # 解码Token
            payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
            current_user = User.query.get(payload['user_id'])
            
            if not current_user or not current_user.is_active:
                return jsonify({
                    'code': 401,
                    'msg': '用户不存在或已被禁用'
                }), 401
            
        except jwt.ExpiredSignatureError:
            return jsonify({
                'code': 401,
                'msg': 'Token已过期'
            }), 401
        except jwt.InvalidTokenError:
            return jsonify({
                'code': 401,
                'msg': 'Token无效'
            }), 401
        
        # 将当前用户信息传递给视图函数
        return f(current_user, *args, **kwargs)
    
    return decorated


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    用户登录
    
    POST /api/v1/auth/login
    Body: {"username": "admin", "password": "admin123"}
    
    Returns:
        JSON: {"code": 200, "msg": "登录成功", "data": {"token": "...", "user_info": {...}}}
    """
    try:
        # 获取请求数据
        data = request.get_json()
        
        if not data:
            return jsonify({
                'code': 400,
                'msg': '请求数据为空'
            }), 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        # 验证必填字段
        if not username or not password:
            return jsonify({
                'code': 400,
                'msg': '用户名和密码不能为空'
            }), 400
        
        # 查询用户
        user = User.query.filter_by(username=username).first()
        
        if not user:
            return jsonify({
                'code': 401,
                'msg': '用户名或密码错误'
            }), 401
        
        # 验证密码
        if not user.check_password(password):
            return jsonify({
                'code': 401,
                'msg': '用户名或密码错误'
            }), 401
        
        # 检查用户状态
        if not user.is_active:
            return jsonify({
                'code': 403,
                'msg': '账号已被禁用，请联系管理员'
            }), 403
        
        # 生成Token
        token = create_token(user.id, user.username, user.role)
        
        # 返回成功响应
        return jsonify({
            'code': 200,
            'msg': '登录成功',
            'data': {
                'token': token,
                'user_info': {
                    'id': user.id,
                    'username': user.username,
                    'role': user.role,
                    'email': user.email
                }
            }
        }), 200
        
    except Exception as e:
        print(f"[登录异常] {e}")
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}'
        }), 500


@auth_bp.route('/verify', methods=['GET'])
@token_required
def verify_token(current_user):
    """
    验证Token有效性
    
    GET /api/v1/auth/verify
    Header: Authorization: Bearer <token>
    
    Returns:
        JSON: {"code": 200, "msg": "Token有效", "data": {"user_info": {...}}}
    """
    return jsonify({
        'code': 200,
        'msg': 'Token有效',
        'data': {
            'user_info': current_user.to_dict()
        }
    }), 200


@auth_bp.route('/change_password', methods=['POST'])
@token_required
def change_password(current_user):
    """
    修改密码
    
    POST /api/v1/auth/change_password
    Header: Authorization: Bearer <token>
    Body: {"old_password": "...", "new_password": "..."}
    
    Returns:
        JSON: {"code": 200, "msg": "密码修改成功"}
    """
    try:
        data = request.get_json()
        old_password = data.get('old_password', '')
        new_password = data.get('new_password', '')
        
        if not old_password or not new_password:
            return jsonify({
                'code': 400,
                'msg': '旧密码和新密码不能为空'
            }), 400
        
        # 验证旧密码
        if not current_user.check_password(old_password):
            return jsonify({
                'code': 401,
                'msg': '旧密码错误'
            }), 401
        
        # 设置新密码
        current_user.set_password(new_password)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'msg': '密码修改成功'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"[修改密码异常] {e}")
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}'
        }), 500
