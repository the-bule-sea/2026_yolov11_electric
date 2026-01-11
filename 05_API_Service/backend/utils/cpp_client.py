"""
C++ 推理服务客户端
用于与WSL中的C++推理引擎通信
"""
import requests
from typing import Dict, List, Optional, Any
from utils.path_utils import convert_path_to_wsl


class CPPInferenceClient:
    """C++ 推理服务客户端"""
    
    def __init__(self, base_url: str, timeout: int = 30):
        """
        初始化C++服务客户端
        
        Args:
            base_url: C++服务基础URL, 例如 http://localhost:8080
            timeout: 请求超时时间(秒)
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
    
    def health_check(self) -> Dict[str, Any]:
        """
        健康检查 - 检查C++服务是否运行
        
        Returns:
            服务状态信息
            
        Example:
            {
                "status": "running",
                "model": "YOLOv11-Nodecode",
                "device": "CUDA:0"
            }
        """
        try:
            response = requests.get(
                f"{self.base_url}/health",
                timeout=5  # 健康检查使用较短超时
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "status": "error",
                    "message": f"HTTP {response.status_code}"
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "status": "unreachable",
                "message": str(e)
            }
    
    def predict(self, image_path: str, conf_threshold: float = 0.25, 
                auto_convert_path: bool = True) -> Optional[Dict[str, Any]]:
        """
        执行推理
        
        Args:
            image_path: 图片路径 (Windows路径或WSL路径)
            conf_threshold: 置信度阈值
            auto_convert_path: 是否自动转换Windows路径为WSL路径
            
        Returns:
            推理结果字典，失败返回None
            
        Example Response:
            {
                "code": 0,
                "message": "success",
                "data": [
                    {
                        "class_id": 0,
                        "label": "insulator_broken",
                        "confidence": 0.882,
                        "bbox": [102, 205, 300, 410]
                    }
                ]
            }
        """
        # 自动转换路径
        if auto_convert_path and ':' in image_path:
            wsl_path = convert_path_to_wsl(image_path)
            print(f"[C++客户端] 路径转换: {image_path} -> {wsl_path}")
        else:
            wsl_path = image_path
        
        # 构建请求数据
        request_data = {
            "image_path": wsl_path,
            "conf_threshold": conf_threshold
        }
        
        try:
            # 发送POST请求
            response = requests.post(
                f"{self.base_url}/predict",
                json=request_data,
                timeout=self.timeout
            )
            
            # 检查HTTP状态码
            if response.status_code != 200:
                print(f"[C++客户端] HTTP错误: {response.status_code}")
                return None
            
            # 解析JSON响应
            result = response.json()
            
            # 检查C++内部状态码
            if result.get('code') != 0:
                print(f"[C++客户端] C++服务错误: {result.get('message')}")
                return None
            
            print(f"[C++客户端] 推理成功，检测到 {len(result.get('data', []))} 个目标")
            return result
            
        except requests.exceptions.Timeout:
            print(f"[C++客户端] 请求超时 (>{self.timeout}s)")
            return None
            
        except requests.exceptions.RequestException as e:
            print(f"[C++客户端] 请求异常: {e}")
            return None
            
        except ValueError as e:
            print(f"[C++客户端] JSON解析失败: {e}")
            return None
    
    def ping(self) -> bool:
        """
        快速检查C++服务是否可达
        
        Returns:
            可达返回True，否则返回False
        """
        result = self.health_check()
        return result.get('status') == 'running'


# 单例模式 - 在app.py中初始化
cpp_client: Optional[CPPInferenceClient] = None


def init_cpp_client(base_url: str, timeout: int = 30) -> CPPInferenceClient:
    """
    初始化全局C++客户端
    
    Args:
        base_url: C++服务基础URL
        timeout: 请求超时时间
        
    Returns:
        CPPInferenceClient实例
    """
    global cpp_client
    cpp_client = CPPInferenceClient(base_url, timeout)
    return cpp_client


def get_cpp_client() -> CPPInferenceClient:
    """
    获取全局C++客户端
    
    Returns:
        CPPInferenceClient实例
    """
    if cpp_client is None:
        raise RuntimeError("C++客户端未初始化，请先调用 init_cpp_client()")
    return cpp_client
