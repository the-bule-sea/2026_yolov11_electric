from ultralytics import YOLO
import cv2

# 1. 加载你刚才训练好的“高材生”模型
# 注意：把下面的路径换成你真实的 best.pt 路径
model_path = r'D:\Document\000_school\2025_4up\yolo_electric\02_Training_PyTorch/runs/train/exp_4060_v3/weights/best.pt'
model = YOLO(model_path)

# 2. 指定一张图片进行测试
# 你可以找一张没参与训练的网图，或者验证集里的图
source_image = r'D:\Document\000_school\2025_4up\yolo_electric\02_Training_PyTorch/test_images\test10.jpg' # 换成你具体的图片路径

# 3. 开始推理
# conf=0.25: 置信度阈值，只有超过 25% 把握的才画框
# save=True: 结果自动保存到 runs/detect 文件夹
# show=True: 运行时直接弹窗显示结果
results = model.predict(source=source_image, save=True, show=True, conf=0.25)

print("推理完成！请去 runs/detect 文件夹查看结果。")