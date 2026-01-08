from ultralytics import YOLO
import os
from pathlib import Path

# ========== 配置区 ==========
# 1. 训练好的模型路径（根据你的实际情况修改）
MODEL_PATH = r'D:\Document\000_school\2025_4up\yolo_electric\02_Training_PyTorch\runs\train\exp_4060_v3\weights\best.pt'

# 2. 测试图片目录（使用脚本所在目录的相对路径）
# 获取脚本所在目录
SCRIPT_DIR = Path(__file__).parent
TEST_IMAGES_DIR = SCRIPT_DIR / 'test_images'

# 3. 置信度阈值（只显示置信度超过此值的检测结果）
CONFIDENCE_THRESHOLD = 0.25

# ========== 主程序 ==========
if __name__ == '__main__':
    # 1. 加载训练好的模型
    print(f"正在加载模型: {MODEL_PATH}")
    model = YOLO(MODEL_PATH)
    print("模型加载成功！\n")
    
    # 2. 获取测试图片目录中的所有图片
    test_dir = Path(TEST_IMAGES_DIR)
    
    # 支持的图片格式
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.webp']
    
    # 查找所有测试图片
    test_images = []
    for ext in image_extensions:
        test_images.extend(test_dir.glob(f'*{ext}'))
        test_images.extend(test_dir.glob(f'*{ext.upper()}'))
    
    if not test_images:
        print(f" 错误：在 {TEST_IMAGES_DIR} 目录中未找到任何图片文件")
        print(f" 支持的格式：{', '.join(image_extensions)}")
        exit(1)
    
    print(f" 找到 {len(test_images)} 张测试图片:")
    for img in test_images:
        print(f"   - {img.name}")
    print()
    
    # 3. 批量推理
    print(" 开始批量推理...\n")
    
    # YOLO 支持直接传入目录路径进行批量推理
    results = model.predict(
        source=TEST_IMAGES_DIR,      # 直接指定目录
        save=True,                    # 保存结果到 runs/detect
        conf=CONFIDENCE_THRESHOLD,    # 置信度阈值
        # project='runs/detect',        # 结果保存项目路径
        name='batch_test',            # 本次推理的名称
    )
    
    # 4. 打印推理统计信息
    print("\n" + "="*50)
    print(" 批量推理完成！")
    print(f" 结果已保存到: runs/detect/batch_test")
    print(f" 共处理 {len(results)} 张图片")
    print("="*50)