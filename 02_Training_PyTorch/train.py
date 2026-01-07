from ultralytics import YOLO
import torch

if __name__ == '__main__':
    # 1. 检查显卡 (你的 4060 应该显示 True)
    print(f"CUDA status: {torch.cuda.is_available()}")
    
    # 2. 加载模型
    # yolo11n.pt 是最快的，yolo11s.pt 精度稍高。
    # 鉴于你要做缺陷检测（小目标），建议先用 n 跑通，如果效果不好换 s 或 m
    model = YOLO('yolo11n.pt') 

    # 3. 开始训练 (包含任务书要求的所有预处理)
    # data: 指向刚才写的 yaml 文件
    results = model.train(
        data=r'D:\Document\000_school\2025_4up\yolo_electric\01_Dataset\data.yaml', # 改成你的绝对路径
        
        # --- 基础配置 ---
        imgsz=640,      # 【图像尺寸统一化】自动将所有图缩放/填充到 640x640
        epochs=100,     # 训练轮数，建议 100-300
        batch=16,       # 4060 8G显存可以开 16 或 32，如果爆显存就改小
        device=0,       # 指定使用显卡
        workers=4,      # 数据加载线程数
        
        # --- 【任务书要求的 数据增强】 ---
        degrees=10.0,   # 【旋转】随机旋转 +/- 10度
        fliplr=0.5,     # 【翻转】50%概率水平翻转 (左右对称的绝缘子很适合)
        flipud=0.0,     # 垂直翻转 (看情况，如果你的图都是正着拍的，设为 0.0)
        hsv_h=0.015,    # 【色彩调整】色调随机变化
        hsv_s=0.7,      # 【色彩调整】饱和度随机变化
        hsv_v=0.4,      # 【色彩调整】亮度随机变化
        mosaic=1.0,     # 马赛克增强 (YOLO核心增强，拼接4张图，强烈建议开启)
        
        # --- 结果保存 ---
        project='runs/train', # 训练结果保存在哪里
        name='exp_4060_v1',   # 实验名称
    )