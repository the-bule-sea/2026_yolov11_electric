"""
图像处理工具
用于在检测结果图片上绘制边界框和标签
"""
import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional


class ImageProcessor:
    """图像处理器"""
    
    # 预定义颜色 (BGR格式)
    COLORS = [
        (255, 0, 0),      # 蓝色
        (0, 255, 0),      # 绿色
        (0, 0, 255),      # 红色
        (255, 255, 0),    # 青色
        (255, 0, 255),    # 品红
        (0, 255, 255),    # 黄色
        (128, 0, 128),    # 紫色
        (255, 165, 0),    # 橙色
    ]
    
    def __init__(self, class_labels: Dict[int, str]):
        """
        初始化图像处理器
        
        Args:
            class_labels: 类别ID到类别名称的映射
        """
        self.class_labels = class_labels
    
    def get_color(self, class_id: int) -> Tuple[int, int, int]:
        """
        根据类别ID获取颜色
        
        Args:
            class_id: 类别ID
            
        Returns:
            BGR颜色元组
        """
        return self.COLORS[class_id % len(self.COLORS)]
    
    def draw_detection_boxes(self, image_path: str, detections: List[Dict],
                            output_path: str, draw_label: bool = True,
                            box_thickness: int = 2) -> bool:
        """
        在图片上绘制检测框
        
        Args:
            image_path: 输入图片路径
            detections: 检测结果列表，每个元素包含 class_id, label, confidence, bbox
            output_path: 输出图片路径
            draw_label: 是否绘制标签文本
            box_thickness: 边框粗细
            
        Returns:
            成功返回True，失败返回False
            
        Example detections:
            [
                {
                    "class_id": 0,
                    "label": "insulator_broken",
                    "confidence": 0.882,
                    "bbox": [102, 205, 300, 410]  # [x1, y1, x2, y2]
                }
            ]
        """
        try:
            # 读取图片
            image = cv2.imread(image_path)
            if image is None:
                print(f"[图像处理] 无法读取图片: {image_path}")
                return False
            
            # 遍历所有检测结果
            for det in detections:
                class_id = det.get('class_id', 0)
                label = det.get('label', 'unknown')
                confidence = det.get('confidence', 0.0)
                bbox = det.get('bbox', [])
                
                # 检查bbox格式
                if len(bbox) != 4:
                    print(f"[图像处理] bbox格式错误: {bbox}")
                    continue
                
                # 解析坐标
                x1, y1, x2, y2 = map(int, bbox)
                
                # 获取颜色
                color = self.get_color(class_id)
                
                # 绘制矩形框
                cv2.rectangle(image, (x1, y1), (x2, y2), color, box_thickness)
                
                # 绘制标签
                if draw_label:
                    # 构建标签文本
                    label_text = f"{label}: {confidence:.2f}"
                    
                    # 计算文本大小
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    font_scale = 0.6
                    font_thickness = 2
                    (text_width, text_height), baseline = cv2.getTextSize(
                        label_text, font, font_scale, font_thickness
                    )
                    
                    # 绘制标签背景
                    cv2.rectangle(
                        image,
                        (x1, y1 - text_height - baseline - 5),
                        (x1 + text_width, y1),
                        color,
                        -1  # 填充
                    )
                    
                    # 绘制标签文本
                    cv2.putText(
                        image,
                        label_text,
                        (x1, y1 - baseline - 5),
                        font,
                        font_scale,
                        (255, 255, 255),  # 白色文字
                        font_thickness
                    )
            
            # 保存结果图片
            success = cv2.imwrite(output_path, image)
            
            if success:
                print(f"[图像处理] 结果图片已保存: {output_path}")
                return True
            else:
                print(f"[图像处理] 保存结果图片失败: {output_path}")
                return False
                
        except Exception as e:
            print(f"[图像处理] 绘制检测框异常: {e}")
            return False
    
    def resize_image(self, image_path: str, output_path: str,
                    max_width: int = 1920, max_height: int = 1080) -> bool:
        """
        调整图片大小 (保持宽高比)
        
        Args:
            image_path: 输入图片路径
            output_path: 输出图片路径
            max_width: 最大宽度
            max_height: 最大高度
            
        Returns:
            成功返回True，失败返回False
        """
        try:
            image = cv2.imread(image_path)
            if image is None:
                return False
            
            h, w = image.shape[:2]
            
            # 计算缩放比例
            scale = min(max_width / w, max_height / h, 1.0)
            
            if scale < 1.0:
                new_w = int(w * scale)
                new_h = int(h * scale)
                resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
                cv2.imwrite(output_path, resized)
            else:
                # 不需要缩放，直接复制
                cv2.imwrite(output_path, image)
            
            return True
            
        except Exception as e:
            print(f"[图像处理] 调整图片大小异常: {e}")
            return False


# 单例模式
image_processor: Optional[ImageProcessor] = None


def init_image_processor(class_labels: Dict[int, str]) -> ImageProcessor:
    """
    初始化全局图像处理器
    
    Args:
        class_labels: 类别标签映射
        
    Returns:
        ImageProcessor实例
    """
    global image_processor
    image_processor = ImageProcessor(class_labels)
    return image_processor


def get_image_processor() -> ImageProcessor:
    """
    获取全局图像处理器
    
    Returns:
        ImageProcessor实例
    """
    if image_processor is None:
        raise RuntimeError("图像处理器未初始化，请先调用 init_image_processor()")
    return image_processor
