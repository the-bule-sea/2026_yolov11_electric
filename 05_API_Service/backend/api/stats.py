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
