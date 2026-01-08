from ultralytics import YOLO
model_path = r'D:\Document\000_school\2025_4up\yolo_electric\02_Training_PyTorch\runs\train\exp_4060_v3\weights/best.pt'
model = YOLO(model_path)
success = model.export(format="onnx", dynamic=True, simplify=True)