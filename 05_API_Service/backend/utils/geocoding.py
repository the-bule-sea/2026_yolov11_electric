"""
逆地理编码工具
将GPS坐标转换为详细地址信息
"""
import requests
from typing import Optional, Dict


class GeocodingClient:
    """逆地理编码客户端"""
    
    def __init__(self):
        """初始化逆地理编码客户端"""
        self.base_url = "http://124.222.204.22/api/other/jwjuhe2.php"
        self.api_id = "88888888"
        self.api_key = "88888888"
        self.timeout = 3  # 3秒超时
    
    def get_address(self, longitude: float, latitude: float) -> Optional[Dict]:
        """
        根据经纬度获取地址信息
        
        Args:
            longitude: 经度
            latitude: 纬度
            
        Returns:
            dict: 地址信息，包含county、town等字段，失败返回None
            
        Example:
            >>> client = GeocodingClient()
            >>> result = client.get_address(121.89062, 30.903636)
            >>> print(result['county'], result['town'])
            浦东新区 南汇新城镇
        """
        try:
            # 构建请求参数
            params = {
                'id': self.api_id,
                'key': self.api_key,
                'lon': longitude,
                'lat': latitude
            }
            
            # 发送请求
            response = requests.get(
                self.base_url,
                params=params,
                timeout=self.timeout
            )
            
            # 检查响应状态
            if response.status_code != 200:
                print(f"[逆地理编码] API返回错误状态码: {response.status_code}")
                return None
            
            # 解析JSON
            data = response.json()
            
            # 检查业务状态码
            if data.get('code') != 200:
                print(f"[逆地理编码] API返回错误: code={data.get('code')}")
                return None
            
            # 返回地址信息
            print(f"[逆地理编码] 成功获取地址: {data.get('county', '')}{data.get('town', '')}")
            return data
            
        except requests.exceptions.Timeout:
            print(f"[逆地理编码] 请求超时")
            return None
        except requests.exceptions.RequestException as e:
            print(f"[逆地理编码] 请求失败: {e}")
            return None
        except Exception as e:
            print(f"[逆地理编码异常] {e}")
            return None
    
    def get_location_name(self, longitude: float, latitude: float) -> str:
        """
        获取简短的地点名称（县区+乡镇）
        
        Args:
            longitude: 经度
            latitude: 纬度
            
        Returns:
            str: 地点名称，如"浦东新区南汇新城镇"，失败返回空字符串
        """
        address_info = self.get_address(longitude, latitude)
        
        if not address_info:
            return ""
        
        # 拼接县区和乡镇
        county = address_info.get('county', '').strip()
        town = address_info.get('town', '').strip()
        
        # 组合名称
        if county and town:
            return f"{county}{town}"
        elif county:
            return county
        elif town:
            return town
        else:
            return ""


# 全局单例
_geocoding_client_instance = None


def get_geocoding_client() -> GeocodingClient:
    """
    获取逆地理编码客户端单例
    
    Returns:
        GeocodingClient: 逆地理编码客户端实例
    """
    global _geocoding_client_instance
    if _geocoding_client_instance is None:
        _geocoding_client_instance = GeocodingClient()
    return _geocoding_client_instance


# 便捷函数
def get_location_name_from_gps(longitude: float, latitude: float) -> str:
    """
    便捷函数：从GPS坐标获取地点名称
    
    Args:
        longitude: 经度
        latitude: 纬度
        
    Returns:
        str: 地点名称
    """
    client = get_geocoding_client()
    return client.get_location_name(longitude, latitude)
