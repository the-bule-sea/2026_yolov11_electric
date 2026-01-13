"""
EXIF信息解析工具
用于从图片中提取GPS经纬度等元数据
"""
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from typing import Optional, Dict
import os


class ExifParser:
    """EXIF信息解析器"""
    
    def __init__(self):
        """初始化EXIF解析器"""
        pass
    
    def extract_gps(self, image_path: str) -> Optional[Dict[str, float]]:
        """
        从图片中提取GPS坐标信息
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            dict: {'latitude': float, 'longitude': float} 或 None
            
        Example:
            >>> parser = ExifParser()
            >>> gps = parser.extract_gps('/path/to/image.jpg')
            >>> print(gps)
            {'latitude': 30.90, 'longitude': 121.89}
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(image_path):
                print(f"[EXIF解析] 文件不存在: {image_path}")
                return None
            
            # 打开图片
            image = Image.open(image_path)
            
            # 获取EXIF数据
            exif_data = image._getexif()
            
            if not exif_data:
                print(f"[EXIF解析] 图片无EXIF数据: {os.path.basename(image_path)}")
                return None
            
            # 查找GPS信息
            gps_info = None
            for tag_id, value in exif_data.items():
                tag_name = TAGS.get(tag_id, tag_id)
                if tag_name == 'GPSInfo':
                    gps_info = value
                    break
            
            if not gps_info:
                print(f"[EXIF解析] 图片无GPS信息: {os.path.basename(image_path)}")
                return None
            
            # 解析GPS数据
            gps_data = {}
            for key, value in gps_info.items():
                tag_name = GPSTAGS.get(key, key)
                gps_data[tag_name] = value

            # print
            print(f"[gps信息]: {gps_data}")
            
            # 提取经纬度
            latitude = self._convert_to_degrees(gps_data.get('GPSLatitude'))
            longitude = self._convert_to_degrees(gps_data.get('GPSLongitude'))
            
            # 处理南纬和西经（需要变为负数）
            if gps_data.get('GPSLatitudeRef') == 'S':
                latitude = -latitude
            if gps_data.get('GPSLongitudeRef') == 'W':
                longitude = -longitude
            
            if latitude is None or longitude is None:
                print(f"[EXIF解析] GPS坐标解析失败: {os.path.basename(image_path)}")
                return None
            
            # 智能检测和纠正：某些相机/软件可能会把经纬度对调
            # 纬度范围: -90 ~ +90，经度范围: -180 ~ +180
            if abs(latitude) > 90 or abs(longitude) > 180:
                print(f"[EXIF解析] 检测到GPS坐标异常，尝试自动纠正...")
                print(f"   原始: 纬度={latitude}, 经度={longitude}")
                
                # 如果纬度超过90度，很可能是和经度对调了
                if abs(latitude) > 90 and abs(longitude) <= 90:
                    latitude, longitude = longitude, latitude
                    print(f"   纠正后: 纬度={latitude}, 经度={longitude}")
                else:
                    print(f"[EXIF解析] GPS坐标超出合理范围，无法自动纠正")
                    return None
            
            print(f"[EXIF解析] 成功提取GPS: 纬度={latitude:.6f}, 经度={longitude:.6f}")
            
            return {
                'latitude': round(latitude, 6),   # 保留6位小数，精度约0.1米
                'longitude': round(longitude, 6)
            }
            
        except AttributeError:
            # 某些图片格式不支持_getexif()
            print(f"[EXIF解析] 图片格式不支持EXIF: {os.path.basename(image_path)}")
            return None
        except Exception as e:
            print(f"[EXIF解析异常] {os.path.basename(image_path)}: {e}")
            return None
    
    def _convert_to_degrees(self, value) -> Optional[float]:
        """
        将GPS坐标从度分秒格式转换为十进制度格式
        
        支持两种格式:
        1. 标准EXIF格式: ((度分子, 度分母), (分分子, 分分母), (秒分子, 秒分母))
        2. 简化格式: (度, 分, 秒) - 直接的浮点数元组
        
        Args:
            value: GPS坐标值
            
        Returns:
            float: 十进制度数 或 None
            
        Example:
            >>> _convert_to_degrees(((31, 1), (14, 1), (4512, 100)))
            31.2458666...
            >>> _convert_to_degrees((31.0, 14.0, 45.12))
            31.2458666...
        """
        if not value:
            return None
        
        try:
            # 检查第一个元素的类型来判断格式
            if isinstance(value[0], (tuple, list)):
                # 标准EXIF格式: ((度分子, 度分母), (分分子, 分分母), (秒分子, 秒分母))
                d = float(value[0][0]) / float(value[0][1])  # 度
                m = float(value[1][0]) / float(value[1][1])  # 分
                s = float(value[2][0]) / float(value[2][1])  # 秒
            else:
                # 简化格式: (度, 分, 秒) - 直接的数值
                d = float(value[0])  # 度
                m = float(value[1])  # 分
                s = float(value[2])  # 秒
            
            # 转换为十进制度: 度 + 分/60 + 秒/3600
            return d + (m / 60.0) + (s / 3600.0)
        except (IndexError, ZeroDivisionError, TypeError, ValueError) as e:
            print(f"[EXIF解析] GPS坐标格式转换失败: {e}, value={value}")
            return None
    
    def extract_all_exif(self, image_path: str) -> Optional[Dict]:
        """
        提取图片的所有EXIF信息（用于调试）
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            dict: 所有EXIF标签及其值 或 None
        """
        try:
            image = Image.open(image_path)
            exif_data = image._getexif()
            
            if not exif_data:
                return None
            
            exif_dict = {}
            for tag_id, value in exif_data.items():
                tag_name = TAGS.get(tag_id, tag_id)
                exif_dict[tag_name] = str(value)
            
            return exif_dict
        except Exception as e:
            print(f"[EXIF解析异常] {e}")
            return None


# 全局单例
_exif_parser_instance = None


def get_exif_parser() -> ExifParser:
    """
    获取EXIF解析器单例
    
    Returns:
        ExifParser: EXIF解析器实例
    """
    global _exif_parser_instance
    if _exif_parser_instance is None:
        _exif_parser_instance = ExifParser()
    return _exif_parser_instance


# 便捷函数
def extract_gps_from_image(image_path: str) -> Optional[Dict[str, float]]:
    """
    便捷函数：从图片提取GPS坐标
    
    Args:
        image_path: 图片路径
        
    Returns:
        dict: {'latitude': float, 'longitude': float} 或 None
    """
    parser = get_exif_parser()
    return parser.extract_gps(image_path)
