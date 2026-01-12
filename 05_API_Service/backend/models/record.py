"""
检测记录模型
存储每次推理的结果、图片URL、缺陷信息等
"""
from models import db
from datetime import datetime
import json


class Record(db.Model):
    """检测记录表"""
    
    __tablename__ = 'records'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # 用户信息
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # 文件信息
    filename = db.Column(db.String(255), nullable=False)
    oss_url = db.Column(db.String(512), nullable=False)  # 原图OSS链接
    result_oss_url = db.Column(db.String(512), nullable=True)  # 结果图OSS链接
    
    # 推理信息
    model_type = db.Column(db.String(50), default='v11-nodecode-fp32')
    inference_time_ms = db.Column(db.Float, nullable=True)  # 推理耗时(毫秒)
    conf_threshold = db.Column(db.Float, default=0.25)
    
    # 检测结果
    defect_count = db.Column(db.Integer, default=0)  # 缺陷总数
    objects_json = db.Column(db.Text, nullable=True)  # JSON格式的检测详情
    defect_summary = db.Column(db.String(255), nullable=True)  # 缺陷摘要，如 "破损(1), 鸟巢(2)"
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.now, index=True)
    
    def set_objects(self, objects: list):
        """设置检测对象列表（自动序列化为JSON）"""
        self.objects_json = json.dumps(objects, ensure_ascii=False)
        self.defect_count = len(objects)
        
        # 生成缺陷摘要
        self.generate_defect_summary(objects)
    
    def get_objects(self) -> list:
        """获取检测对象列表（自动反序列化）"""
        if self.objects_json:
            return json.loads(self.objects_json)
        return []
    
    def generate_defect_summary(self, objects: list):
        """生成缺陷摘要"""
        if not objects:
            self.defect_summary = "无缺陷"
            return
        
        # 统计各类别数量
        label_counts = {}
        for obj in objects:
            label = obj.get('label', 'unknown')
            label_counts[label] = label_counts.get(label, 0) + 1
        
        # 生成摘要文本
        summary_parts = [f"{label}({count})" for label, count in label_counts.items()]
        self.defect_summary = ", ".join(summary_parts)
    
    def to_dict(self, include_objects=False):
        """转换为字典"""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'filename': self.filename,
            'oss_url': self.oss_url,
            'result_oss_url': self.result_oss_url,
            'model_type': self.model_type,
            'inference_time_ms': self.inference_time_ms,
            'conf_threshold': self.conf_threshold,
            'defect_count': self.defect_count,
            'defect_summary': self.defect_summary,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
        }
        
        if include_objects:
            data['objects'] = self.get_objects()
        
        return data
    
    def __repr__(self):
        return f'<Record {self.id} - {self.filename}>'
