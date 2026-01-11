"""
历史记录模块 API
提供检测记录的查询、详情、删除等功能
"""
from flask import request, jsonify
from api import records_bp
from api.auth import token_required
from models import db
from models.record import Record
from datetime import datetime


@records_bp.route('/list', methods=['GET'])
@token_required
def get_records_list(current_user):
    """
    获取检测记录列表（分页+筛选）
    
    GET /api/v1/records/list?page=1&page_size=10&date_start=2026-01-01
    Header: Authorization: Bearer <token>
    
    Query Params:
        - page: 页码，默认1
        - page_size: 每页数量，默认10
        - date_start: 起始日期，格式YYYY-MM-DD，可选
        - date_end: 结束日期，格式YYYY-MM-DD，可选
    
    Returns:
        JSON: {
            "code": 200,
            "msg": "success",
            "data": {
                "total": 50,
                "page": 1,
                "page_size": 10,
                "list": [...]
            }
        }
    """
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)
        date_start = request.args.get('date_start', None)
        date_end = request.args.get('date_end', None)
        
        # 限制每页最大数量
        page_size = min(page_size, 100)
        
        # 构建查询
        query = Record.query
        
        # 如果不是管理员，只能查看自己的记录
        if current_user.role != 'admin':
            query = query.filter_by(user_id=current_user.id)
        
        # 日期筛选
        if date_start:
            try:
                start_date = datetime.strptime(date_start, '%Y-%m-%d')
                query = query.filter(Record.created_at >= start_date)
            except ValueError:
                return jsonify({
                    'code': 400,
                    'msg': '日期格式错误，请使用 YYYY-MM-DD'
                }), 400
        
        if date_end:
            try:
                end_date = datetime.strptime(date_end, '%Y-%m-%d')
                # 包含当天的所有记录
                from datetime import timedelta
                end_date = end_date + timedelta(days=1)
                query = query.filter(Record.created_at < end_date)
            except ValueError:
                return jsonify({
                    'code': 400,
                    'msg': '日期格式错误，请使用 YYYY-MM-DD'
                }), 400
        
        # 按创建时间倒序排序
        query = query.order_by(Record.created_at.desc())
        
        # 分页
        pagination = query.paginate(page=page, per_page=page_size, error_out=False)
        
        # 构建返回数据
        records_list = [record.to_dict() for record in pagination.items]
        
        return jsonify({
            'code': 200,
            'msg': 'success',
            'data': {
                'total': pagination.total,
                'page': page,
                'page_size': page_size,
                'total_pages': pagination.pages,
                'list': records_list
            }
        }), 200
        
    except Exception as e:
        print(f"[记录列表查询异常] {e}")
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}'
        }), 500


@records_bp.route('/detail/<int:record_id>', methods=['GET'])
@token_required
def get_record_detail(current_user, record_id):
    """
    获取单条记录详情
    
    GET /api/v1/records/detail/<record_id>
    Header: Authorization: Bearer <token>
    
    Returns:
        JSON: {
            "code": 200,
            "msg": "success",
            "data": {
                "id": 1024,
                "filename": "test.jpg",
                "objects": [...],
                ...
            }
        }
    """
    try:
        record = Record.query.get(record_id)
        
        if not record:
            return jsonify({
                'code': 404,
                'msg': '记录不存在'
            }), 404
        
        # 权限检查：非管理员只能查看自己的记录
        if current_user.role != 'admin' and record.user_id != current_user.id:
            return jsonify({
                'code': 403,
                'msg': '无权访问此记录'
            }), 403
        
        return jsonify({
            'code': 200,
            'msg': 'success',
            'data': record.to_dict(include_objects=True)
        }), 200
        
    except Exception as e:
        print(f"[记录详情查询异常] {e}")
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}'
        }), 500


@records_bp.route('/delete/<int:record_id>', methods=['DELETE'])
@token_required
def delete_record(current_user, record_id):
    """
    删除记录
    
    DELETE /api/v1/records/delete/<record_id>
    Header: Authorization: Bearer <token>
    
    Returns:
        JSON: {"code": 200, "msg": "删除成功"}
    """
    try:
        record = Record.query.get(record_id)
        
        if not record:
            return jsonify({
                'code': 404,
                'msg': '记录不存在'
            }), 404
        
        # 权限检查：非管理员只能删除自己的记录
        if current_user.role != 'admin' and record.user_id != current_user.id:
            return jsonify({
                'code': 403,
                'msg': '无权删除此记录'
            }), 403
        
        # 删除记录（OSS文件可选择性删除或保留）
        db.session.delete(record)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'msg': '删除成功'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"[记录删除异常] {e}")
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}'
        }), 500
