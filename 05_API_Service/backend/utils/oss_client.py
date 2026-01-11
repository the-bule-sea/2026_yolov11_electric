"""
七牛云OSS上传工具
用于将图片上传到七牛云对象存储
"""
import os
import uuid
from datetime import datetime
from qiniu import Auth, put_file, BucketManager
from typing import Optional


class QiniuOSSClient:
    """七牛云OSS客户端"""
    
    def __init__(self, access_key: str, secret_key: str, bucket_name: str, domain: str):
        """
        初始化七牛云客户端
        
        Args:
            access_key: 七牛云Access Key
            secret_key: 七牛云Secret Key
            bucket_name: 存储空间名称
            domain: CDN域名
        """
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket_name = bucket_name
        self.domain = domain.rstrip('/')  # 移除末尾斜杠
        
        # 创建认证对象
        self.auth = Auth(access_key, secret_key)
        self.bucket_manager = BucketManager(self.auth)
    
    def generate_unique_key(self, original_filename: str, prefix: str = '') -> str:
        """
        生成唯一的文件Key
        
        Args:
            original_filename: 原始文件名
            prefix: 文件名前缀(可选)
            
        Returns:
            唯一的文件Key
            
        Example:
            20260111_uuid_image.jpg
        """
        # 获取文件扩展名
        _, ext = os.path.splitext(original_filename)
        
        # 生成时间戳和UUID
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        
        # 组合文件名
        if prefix:
            key = f"{prefix}/{timestamp}_{unique_id}{ext}"
        else:
            key = f"{timestamp}_{unique_id}{ext}"
        
        return key
    
    def upload_file(self, local_path: str, key: Optional[str] = None, 
                   prefix: str = '') -> Optional[str]:
        """
        上传文件到七牛云
        
        Args:
            local_path: 本地文件绝对路径
            key: 上传到云端的文件名(可选，默认自动生成)
            prefix: 文件名前缀(可选)
            
        Returns:
            成功返回CDN URL，失败返回None
            
        Example:
            >>> client.upload_file('/path/to/image.jpg')
            'http://cdn.your-domain.com/20260111_123456_abc123.jpg'
        """
        # 检查文件是否存在
        if not os.path.exists(local_path):
            print(f"[OSS] 文件不存在: {local_path}")
            return None
        
        # 如果没有指定key，自动生成
        if key is None:
            original_filename = os.path.basename(local_path)
            key = self.generate_unique_key(original_filename, prefix)
        
        # 生成上传凭证 (有效期1小时)
        token = self.auth.upload_token(self.bucket_name, key, 3600)
        
        try:
            # 执行上传
            ret, info = put_file(token, key, local_path)
            
            # 检查上传结果
            if info.status_code == 200:
                cdn_url = f"{self.domain}/{key}"
                print(f"[OSS] 上传成功: {cdn_url}")
                return cdn_url
            else:
                print(f"[OSS] 上传失败: {info}")
                return None
                
        except Exception as e:
            print(f"[OSS] 上传异常: {e}")
            return None
    
    def delete_file(self, key: str) -> bool:
        """
        删除七牛云上的文件
        
        Args:
            key: 文件Key
            
        Returns:
            成功返回True，失败返回False
        """
        try:
            ret, info = self.bucket_manager.delete(self.bucket_name, key)
            if info.status_code == 200:
                print(f"[OSS] 删除成功: {key}")
                return True
            else:
                print(f"[OSS] 删除失败: {info}")
                return False
        except Exception as e:
            print(f"[OSS] 删除异常: {e}")
            return False
    
    def get_file_url(self, key: str) -> str:
        """
        获取文件的CDN URL
        
        Args:
            key: 文件Key
            
        Returns:
            CDN URL
        """
        return f"{self.domain}/{key}"


# 单例模式 - 在app.py中初始化
oss_client: Optional[QiniuOSSClient] = None


def init_oss_client(access_key: str, secret_key: str, 
                    bucket_name: str, domain: str) -> QiniuOSSClient:
    """
    初始化全局OSS客户端
    
    Args:
        access_key: 七牛云Access Key
        secret_key: 七牛云Secret Key
        bucket_name: 存储空间名称
        domain: CDN域名
        
    Returns:
        QiniuOSSClient实例
    """
    global oss_client
    oss_client = QiniuOSSClient(access_key, secret_key, bucket_name, domain)
    return oss_client


def get_oss_client() -> QiniuOSSClient:
    """
    获取全局OSS客户端
    
    Returns:
        QiniuOSSClient实例
    """
    if oss_client is None:
        raise RuntimeError("OSS客户端未初始化，请先调用 init_oss_client()")
    return oss_client
