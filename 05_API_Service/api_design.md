# RESTful API 设计文档

本项目后端推理服务基于 C++ 编写，对外提供 RESTful 接口供前端（Gradio/Web）调用。

## 1. 基础信息
- **Base URL**: `http://<server_ip>:8000/api/v1`
- **Content-Type**: `application/json` 或 `multipart/form-data`

## 2. 接口定义

### 2.1 系统健康检查
**GET** `/health`
- **功能**: 检查服务是否存活，GPU是否就绪。
- **响应**:
  ```json
  {
    "status": "ok",
    "gpu_usage": "15%",
    "model_loaded": true,
    "version": "1.0.0"
  }
  ```

### 2.2 用户鉴权 (User Auth)
**POST** `/auth/login`
- **功能**: 用户登录获取 Token。
- **请求参数**:
  ```json
  {
    "username": "admin",
    "password": "hashed_password_string"
  }
  ```
- **响应**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "token": "eyJhbGciOiJIUzI1...",
      "expire_at": 1735689600
    }
  }
  ```

### 2.3 图像检测 (Image Inference)
**POST** `/detect/image`
- **功能**: 上传单张图片进行缺陷检测。
- **Content-Type**: `multipart/form-data`
- **请求参数**:
  - `file`: 图片文件 (jpg/png)
  - `conf_threshold`: (可选) 置信度阈值，默认 0.25
- **响应**:
  ```json
  {
    "code": 200,
    "time_cost_ms": 15.5,
    "results": [
      {
        "class_id": 1,
        "class_name": "insulator",
        "confidence": 0.95,
        "bbox": [100, 200, 300, 400]  // [x1, y1, x2, y2]
      },
      {
        "class_id": 3,
        "class_name": "damper",
        "confidence": 0.88,
        "bbox": [500, 100, 550, 150]
      }
    ]
  }
  ```

### 2.4 视频流检测 (Video Stream Inference)
**WS (WebSocket)** `/ws/detect/stream`
- **功能**: 实时视频流检测（Web端推荐使用 WebSocket 而非 HTTP POST）。
- **协议**: WebSocket
- **交互流程**:
  1. Client 发送: 二进制图片帧 (JPEG/Bytes)。
  2. Server 返回: 检测后的图片帧 (带框) 或 仅返回检测结果 JSON。
  
> **注意**: 如果使用纯 HTTP 接口模拟视频流，可以使用 `POST /detect/frame`，但在 30FPS 下会有较大网络开销。

### 2.5 获取系统统计 (System Stats)
**GET** `/stats/summary`
- **功能**: 获取今日检测统计数据。
- **响应**:
  ```json
  {
    "total_detected": 150,
    "defects_breakdown": {
      "insulator": 12,
      "damper": 5,
      "plate": 8
    }
  }
  ```

## 3. 错误码定义
- `200`: 成功
- `400`: 请求参数错误
- `401`: 未授权
- `500`: 服务器内部错误 (如 TensorRT 推理失败)
