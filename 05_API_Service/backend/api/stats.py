"""
统计模块 API
提供仪表盘数据、缺陷分布、趋势图等统计功能
"""
from flask import request, jsonify
from api import stats_bp
from api.auth import token_required
from models import db
from models.record import Record
from datetime import datetime, timedelta
from sqlalchemy import func
from utils.cpp_client import get_cpp_client
from utils.geocoding import get_geocoding_client  # 新增: 逆地理编码工具


@stats_bp.route('/dashboard', methods=['GET'])
@token_required
def get_dashboard_stats(current_user):
    """
    获取仪表盘统计数据
    
    GET /api/v1/stats/dashboard
    Header: Authorization: Bearer <token>
    
    Returns:
        JSON: {
            "code": 200,
            "msg": "success",
            "data": {
                "today_check_count": 150,
                "total_defects": 23,
                "defect_distribution": {...},
                "weekly_trend": [...]
            }
        }
    """
    try:
        # 根据角色决定查询范围
        if current_user.role == 'admin':
            base_query = Record.query
        else:
            base_query = Record.query.filter_by(user_id=current_user.id)
        
        # 1. 今日检测总数
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_check_count = base_query.filter(
            Record.created_at >= today_start
        ).count()
        
        # 2. 今日发现缺陷数
        today_records = base_query.filter(
            Record.created_at >= today_start
        ).all()
        
        total_defects_today = sum(record.defect_count for record in today_records)
        
        # 3. 缺陷分布统计（今日）
        defect_distribution = {}
        for record in today_records:
            objects = record.get_objects()
            for obj in objects:
                label = obj.get('label', 'unknown')
                defect_distribution[label] = defect_distribution.get(label, 0) + 1
        
        # 4. 过去7天趋势
        weekly_trend = []
        for i in range(6, -1, -1):  # 从7天前到今天
            day_start = today_start - timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            
            day_defect_count = base_query.filter(
                Record.created_at >= day_start,
                Record.created_at < day_end
            ).with_entities(func.sum(Record.defect_count)).scalar() or 0
            
            weekly_trend.append(int(day_defect_count))
        
        # 5. 总统计（可选）
        total_records = base_query.count()
        total_defects_all = base_query.with_entities(
            func.sum(Record.defect_count)
        ).scalar() or 0
        
        return jsonify({
            'code': 200,
            'msg': 'success',
            'data': {
                'today_check_count': today_check_count,
                'total_defects': total_defects_today,
                'defect_distribution': defect_distribution,
                'weekly_trend': weekly_trend,
                'total_records': total_records,
                'total_defects_all': int(total_defects_all)
            }
        }), 200
        
    except Exception as e:
        print(f"[仪表盘统计异常] {e}")
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}'
        }), 500


@stats_bp.route('/monthly', methods=['GET'])
@token_required
def get_monthly_stats(current_user):
    """
    获取月度统计数据
    
    GET /api/v1/stats/monthly?year=2026&month=1
    Header: Authorization: Bearer <token>
    
    Returns:
        JSON: {
            "code": 200,
            "msg": "success",
            "data": {
                "year": 2026,
                "month": 1,
                "total_checks": 500,
                "total_defects": 80,
                "daily_stats": [...]
            }
        }
    """
    try:
        # 获取年月参数
        year = request.args.get('year', datetime.now().year, type=int)
        month = request.args.get('month', datetime.now().month, type=int)
        
        # 根据角色决定查询范围
        if current_user.role == 'admin':
            base_query = Record.query
        else:
            base_query = Record.query.filter_by(user_id=current_user.id)
        
        # 计算月份起止时间
        month_start = datetime(year, month, 1)
        if month == 12:
            month_end = datetime(year + 1, 1, 1)
        else:
            month_end = datetime(year, month + 1, 1)
        
        # 查询该月所有记录
        monthly_records = base_query.filter(
            Record.created_at >= month_start,
            Record.created_at < month_end
        ).all()
        
        # 统计总数
        total_checks = len(monthly_records)
        total_defects = sum(record.defect_count for record in monthly_records)
        
        # 按天统计
        from collections import defaultdict
        daily_stats = defaultdict(lambda: {'checks': 0, 'defects': 0})
        
        for record in monthly_records:
            day = record.created_at.day
            daily_stats[day]['checks'] += 1
            daily_stats[day]['defects'] += record.defect_count
        
        # 转换为列表格式
        daily_list = [
            {
                'day': day,
                'checks': stats['checks'],
                'defects': stats['defects']
            }
            for day, stats in sorted(daily_stats.items())
        ]
        
        return jsonify({
            'code': 200,
            'msg': 'success',
            'data': {
                'year': year,
                'month': month,
                'total_checks': total_checks,
                'total_defects': total_defects,
                'daily_stats': daily_list
            }
        }), 200
        
    except Exception as e:
        print(f"[月度统计异常] {e}")
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}'
        }), 500


@stats_bp.route('/server', methods=['GET'])
@token_required
def get_server_status(current_user):
    """
    获取C++服务器状态
    
    GET /api/v1/stats/server
    Header: Authorization: Bearer <token>
    
    Returns:
        JSON: {
            "code": 200,
            "msg": "success",
            "data": {
                "status": "running",
                "model": "YOLOv11-Nodecode",
                "device": "CUDA:0"
            }
        }
    """
    try:
        cpp_client = get_cpp_client()
        health_info = cpp_client.health_check()
        
        # 检查C++服务状态
        if health_info.get('status') == 'running':
            return jsonify({
                'code': 200,
                'msg': 'success',
                'data': health_info
            }), 200
        else:
            # C++服务异常但可连接
            return jsonify({
                'code': 503,
                'msg': 'C++服务异常',
                'data': health_info
            }), 503
            
    except Exception as e:
        print(f"[服务器状态查询异常] {e}")
        return jsonify({
            'code': 500,
            'msg': f'无法连接到C++服务: {str(e)}',
            'data': {
                'status': 'unreachable',
                'message': str(e)
            }
        }), 500


@stats_bp.route('/warning', methods=['GET'])
def get_warning_data():
    """
    获取数据大屏实时预警数据
    
    GET /api/v1/stats/warning
    
    功能：
    - 返回最近有缺陷且带GPS定位的检测记录
    - 用于数据大屏的地图展示
    - 支持自动刷新（轮询）
    
    Query Params:
        limit (int): 返回记录数量，默认20，最大100
        hours (int): 查询最近N小时的数据，默认24小时
    
    Returns:
        JSON: {
            "code": 200,
            "msg": "success",
            "data": {
                "list": [
                    {
                        "name": "监测点名称",
                        "lng": 121.89,
                        "lat": 30.90,
                        "value": 2,  // 缺陷数量
                        "timestamp": "14:30:25",
                        "detail": "破损(1), 鸟巢(1)"  // 缺陷详情
                    }
                ]
            }
        }
    """
    try:
        # 获取查询参数
        limit = request.args.get('limit', 20, type=int)
        hours = request.args.get('hours', 24, type=int)
        
        # 限制最大数量
        if limit > 100:
            limit = 100
        
        # 计算时间范围
        time_threshold = datetime.now() - timedelta(hours=hours)
        
        # 查询条件:
        # 1. defect_count > 0 (有缺陷)
        # 2. longitude IS NOT NULL AND latitude IS NOT NULL (有GPS)
        # 3. created_at >= time_threshold (在时间范围内)
        query = Record.query.filter(
            Record.defect_count > 0,
            Record.longitude.isnot(None),
            Record.latitude.isnot(None),
            Record.created_at >= time_threshold
        ).order_by(
            Record.created_at.desc()  # 最新的在前
        ).limit(limit)
        
        records = query.all()
        
        # 构建返回数据
        warning_list = []
        for record in records:
            # 生成地点名称
            # 优先使用数据库中的 location_name（上传时已获取）
            if record.location_name:
                name = record.location_name
            else:
                # location_name为空时使用备选方案
                import os
                name = os.path.splitext(record.filename)[0][:20]
                if not name or name.startswith('tmp') or len(name) > 30:
                    name = f"监测点 #{record.id}"
            
            # 格式化时间戳（只显示时分秒）
            timestamp = record.created_at.strftime('%H:%M:%S')
            
            warning_item = {
                'name': name,
                'lng': record.longitude,
                'lat': record.latitude,
                'value': record.defect_count,
                'timestamp': timestamp,
                'detail': record.defect_summary or '缺陷详情未知',
                'record_id': record.id  # 可选：用于追溯
            }
            
            warning_list.append(warning_item)
        
        return jsonify({
            'code': 200,
            'msg': 'success',
            'data': {
                'list': warning_list,
                'total': len(warning_list),
                'time_range_hours': hours
            }
        }), 200
        
    except Exception as e:
        print(f"[预警数据查询异常] {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}'
        }), 500

