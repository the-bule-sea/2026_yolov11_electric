# 📘 电力巡检系统后端 API 接口文档 (v2.1 完整版)

**—— Windows (Host) + WSL (Inference) 混合架构**

## 1. 系统架构与环境约定 (Architecture & Env)

本系统采用 **微服务架构**，分为业务层和计算层，部署在同一台物理机的不同环境：

* **业务层 (Python/Flask)**: 运行在 **Windows** 主机上。负责用户交互、数据库、文件存储。
* **计算层 (C++/TensorRT)**: 运行在 **WSL (Ubuntu)** 子系统中。负责高性能 AI 推理。
* 存储层 (Local + OSS):
  - 本地 D 盘: 作为“高速缓存”，用于 C++ 极速读取推理（定期清理）。
  - 七牛云 OSS: 作为“持久层”，用于永久保存图片/视频，提供 CDN 加速访问。

### ⚠️ 关键开发约定 (Critical Conventions)

1. **文件共享**: 图片必须存储在 Windows 的 **非系统盘**（如 `D:/` 或 `E:/`），WSL 通过 `/mnt/d/` 自动挂载读取。**严禁**存储在 Windows C 盘系统目录或 WSL 内部文件系统。
2. **路径转换**: Python 在调用 C++ 前，必须将 Windows 路径转换为 WSL 路径。
* *Win*: `D:/当前项目路径/05_API_Service/backend/temp_uploads/test.jpg`
* *WSL*: `/mnt/d/当前项目路径/05_API_Service/backend/temp_uploads/test.jpg`
3. **数据持久化**: 数据库中 只存储 OSS 的 URL，不存储本地 D 盘路径（因为本地文件会被清理）。


3. **网络通信**:
* C++ 服务监听 `0.0.0.0` (允许外部连接)。
* Python 服务通过 `http://localhost:8080` 访问 C++。



---

## 2. 模块一：Python 业务后端 API (对外)

**运行环境**: Windows | **端口**: 5000 | **Base URL**: `http://<server_ip>:5000/api/v1`
### 2.0 整体架构
为了防止代码乱成一团，建议采用 Flask Blueprint (蓝图) 结构：
```mermaid
backend/
├── app.py                # 启动入口 (create_app, run)
├── config.py             # 配置文件 (数据库URL, C++接口地址)
├── requirements.txt      # 依赖包 (flask, requests, sqlalchemy, pymysql)
├── static/               # 部分静态文件目录 (如果用得到)
├── temp_uploads/         # 本地临时存图目录 (D盘)
├── api/                  # 核心代码区
│   ├── __init__.py
│   ├── auth.py           # 对应认证模块接口
│   ├── detect.py         # 对应推理模块接口 (存本地->调C++->传OSS)
│   ├── records.py        # 对应历史记录接口
│   └── stats.py          # 对应统计接口
├── models/               # 数据库模型 (SQLAlchemy)
│   ├── user.py
│   └── record.py
└── utils/                # 工具类
    ├── cpp_client.py     # 专门封装 requests 请求发给 C++
    ├── image_proc.py     # 专门用 cv2 画框
    ├── oss_client.py     # 七牛云上传工具
    └── path_utils.py     # 用于wsl和windows路径转化

```

### 2.1 认证模块 (Auth)

#### 2.1.1 用户登录

**POST** `/auth/login`

* **功能**: 验证账号密码，发放 JWT Token。
* **Request Body**:
```json
{
  "username": "admin",
  "password": "password123"
}

```


* **Response**:
```json
{
  "code": 200,
  "msg": "登录成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "user_info": { "id": 1, "username": "admin", "role": "manager" }
  }
}

```



### 2.2 推理业务模块 (Inference)

#### 2.2.1 上传并检测图片

**POST** `/detect/image`

* **功能**:
1. 接收前端上传的图片并保存到 Windows 磁盘。
2. **自动转换路径**并调用 C++ 引擎。(传 WSL 路径 /mnt/d/当前项目路径/05_API_Service/backend/temp_uploads/uuid.jpg)
3. (异步)将图片上传至 七牛云 OSS
4. 接收结果，绘制检测框，OSS URL存入数据库。
5. 返回处理后的图片 URL 和数据。


* **Header**: `Authorization: Bearer <token>`
* **Content-Type**: `multipart/form-data`
* **Request**:
* `file`: (File) 图片文件
* `model_type`: (String) 可选，例如 "v11-nodecode-fp32" (默认)


* **Response**:
```json
{
  "code": 200,
  "msg": "检测完成",
  "data": {
    "record_id": 1024,
    "oss_url": "http://cdn.your-domain.com/20260111_001.jpg", // 原图 OSS 链接
    "result_oss_url": "http://cdn.your-domain.com/20260111_001_res.jpg", // 结果图 OSS 链接
    "inference_time_ms": 25.5,          // C++返回的耗时
    "defect_count": 2,                  // 缺陷数量统计
    "objects": [                        // 详细检测列表
      {
        "class_id": 0,
        "label": "insulator_broken",    // 类别名称
        "confidence": 0.88,
        "bbox": [100, 200, 300, 400]    // x1, y1, x2, y2
      }
    ]
  }
}

```



#### 2.2.2 批量上传并检测图片

**POST** `/detect/batch`

* **功能**:
1. 接收前端上传的多张图片（一次最多20张）
2. 对每张图片分别调用 C++ 推理引擎
3. 批量上传到七牛云 OSS
4. 批量保存检测记录到数据库
5. 返回所有图片的处理结果


* **Header**: `Authorization: Bearer <token>`
* **Content-Type**: `multipart/form-data`
* **Request**:
* `files`: (File[]) 多个图片文件（字段名都是 files）
* `model_type`: (String) 可选，例如 "v11-nodecode-fp32" (默认)
* `conf_threshold`: (Float) 可选，置信度阈值 (默认 0.25)


* **Response**:
```json
{
  "code": 200,
  "msg": "批量检测完成",
  "data": {
    "total": 3,                    // 总数
    "success": 3,                  // 成功数量
    "failed": 0,                   // 失败数量
    "results": [                   // 每张图片的结果
      {
        "filename": "image1.jpg",
        "status": "success",
        "record_id": 1024,
        "oss_url": "http://cdn.your-domain.com/xxx.jpg",
        "result_oss_url": "http://cdn.your-domain.com/xxx_res.jpg",
        "inference_time_ms": 25.5,
        "defect_count": 2,
        "objects": [...]
      },
      {
        "filename": "image2.jpg",
        "status": "success",
        "record_id": 1025,
        "oss_url": "http://cdn.your-domain.com/yyy.jpg",
        "result_oss_url": "http://cdn.your-domain.com/yyy_res.jpg",
        "inference_time_ms": 23.2,
        "defect_count": 0,
        "objects": []
      },
      {
        "filename": "image3.jpg",
        "status": "failed",
        "error": "推理失败: 图片格式错误"
      }
    ]
  }
}


#### 2.2.3 上传并检测视频

**POST** `/detect/video`

* **功能**:
1. 接收前端上传的视频文件（支持 mp4/avi，最大 500MB）。
2. 保存到 Windows 本地临时目录。
3. 调用 C++ 引擎进行视频推理（自动转换路径）。
4. 将原视频和结果视频上传至 OSS。
5. 保存检测记录到数据库。
6. (注意：视频处理耗时较长，请设置较长的请求超时时间)。


* **Header**: `Authorization: Bearer <token>`
* **Content-Type**: `multipart/form-data`
* **Request**:
* `file`: (File) 视频文件
* `model_type`: (String) 可选，例如 "4060-v3-n-fp32" (默认)
* `conf_threshold`: (Float) 可选，置信度阈值 (默认 0.25)


* **Response**:
```json
{
  "code": 200,
  "msg": "视频检测完成",
  "data": {
    "record_id": 1026,
    "oss_url": "http://cdn.your-domain.com/videos/original/uuid.mp4",        // 原视频 OSS 链接
    "result_oss_url": "http://cdn.your-domain.com/videos/result/uuid_res.mp4", // 结果视频 OSS 链接
    "processing": {                     // 处理统计信息
        "processed_frames": 900,
        "total_detections": 245,
        "processing_time_seconds": 8.5,
        "average_fps": 105.88
    }
  }
}
```



### 2.3 历史记录模块 (Records)

#### 2.3.1 获取检测记录列表

**GET** `/records/list`

* **功能**: 分页获取历史检测记录（支持筛选）。
* **Query Params**:
* `page`: 页码 (默认 1)
* `page_size`: 每页数量 (默认 10)
* `date_start`: 起始日期 (例如 2026-01-01)


* **Response**:
```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "total": 50,
    "list": [
      {
        "id": 1024,
        "upload_time": "2026-01-11 14:30:00",
        "filename": "test.jpg",
        "oss_url": "http://cdn.your-domain.com/test.jpg", // 即使本地文件删了，这里也能访问
        "defect_summary": "破损(1), 鸟巢(1)"
      }
    ]
  }
}

```



### 2.4 数据统计模块 (Stats)

#### 2.4.1 首页仪表盘统计

**GET** `/stats/dashboard`

* **功能**: 获取今日检测量、缺陷分布数据（用于前端图表）。
* **Response**:
```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "today_check_count": 150,           // 今日检测总数
    "total_defects": 23,                // 今日发现缺陷数
    "defect_distribution": {            // 各类别分布(用于饼图)
      "insulator_broken": 10,
      "nest": 5,
      "ring_shifted": 8
    },
    "weekly_trend": [10, 12, 15, 8, 20, 15, 23] // 过去7天趋势
  }
}

```

#### 2.4.2 获取cpp服务器状态(cpp服务接口在下面)

**GET** `/stats/server`

* **功能**: 获取C++服务器状态。
* **Response**:
```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "status": "running", 
    "model": "YOLOv11-Nodecode", 
    "device": "CUDA:0"
  }
}
```

#### 2.4.3 数据大屏获取实时预警 (new)
* **请求示例**
```bash
# 获取最近24小时的20条预警数据
GET http://localhost:5000/api/v1/stats/warning

# 获取最近12小时的10条预警数据
GET http://localhost:5000/api/v1/stats/warning?limit=10&hours=12

# 获取最近1小时的50条预警数据
GET http://localhost:5000/api/v1/stats/warning?limit=50&hours=1
```
**GET** `/stats/warning`

* **功能**: 定时自动更新监测点数据
* **Response**:
```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "list": [
      {
        "name": "监测点 #1024",
        "lng": 121.89,
        "lat": 30.90,
        "value": 2,
        "timestamp": "14:30:25",
        "detail": "破损(1), 鸟巢(1)",
        "record_id": 1024
      },
      {
        "name": "上海电力大学",
        "lng": 121.567706,
        "lat": 31.245944,
        "value": 4,
        "timestamp": "14:25:10",
        "detail": "绝缘子破损(2), 鸟巢(2)",
        "record_id": 1025
      }
    ],
    "total": 2,
    "time_range_hours": 24
  }
}
```

---

## 3. 模块二：C++ 推理引擎 API (内部接口)

**运行环境**: WSL (Ubuntu) | **端口**: 8080 | **Base URL**: `http://localhost:8080`
**注意**: 此接口仅供 Python 后端调用，不对前端开放。

### 3.1 执行推理 (Inference)

**POST** `/predict`

* **功能**: 接收 WSL 格式的绝对路径，读取图片进行推理。
* **Request Body**:
```json
{
  "image_path": "/mnt/d/项目/05_API_Service/backend/temp_uploads/test.jpg", 
  "conf_threshold": 0.25,
  "model_type": "v11-nodecode-fp32"
}

```
`model_type: v11-nodecode-fp32` | `v11-nodecode-int8` | `v11-fp32` | `v11-int8`
`

* *注意*: `image_path` 必须是 `/mnt/...` 开头的路径。


* **Response**:
```json
{
  "code": 0,           // 0 表示 C++ 内部运行正常
  "message": "success",
  "data": [
    {
      "class_id": 0,
      "label": "insulator_broken",
      "confidence": 0.882,
      "bbox": [102, 205, 300, 410] // [left, top, right, bottom]
    }
  ]
}

```



### 3.2 批量执行推理 (Batch Inference)

**POST** `/predict_batch`

* **功能**: 接收多个 WSL 格式的绝对路径，批量读取图片进行推理（性能优化）。
* **Request Body**:
```json
{
  "image_paths": [
    "/mnt/d/项目/05_API_Service/backend/temp_uploads/img1.jpg",
    "/mnt/d/项目/05_API_Service/backend/temp_uploads/img2.jpg",
    "/mnt/d/项目/05_API_Service/backend/temp_uploads/img3.jpg"
  ],
  "conf_threshold": 0.25,
  "model_type": "v11-nodecode-fp32"
}

```

* **注意**: 
  - `image_paths` 必须是数组，每个元素都是 `/mnt/...` 开头的路径
  - 批量大小限制：最多 50 张图片
  - 利用 `commits()` 批量推理，比多次调用 `/predict` 更高效


* **Response**:
```json
{
  "code": 0,
  "message": "success",
  "model_used": "YOLOv11-Nodecode-FP32",
  "total_time_ms": 68.5,
  "batch_size": 3,
  "success_count": 2,
  "failed_count": 1,
  "results": [
    {
      "image_path": "/mnt/d/.../img1.jpg",
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
    },
    {
      "image_path": "/mnt/d/.../img2.jpg",
      "code": 0,
      "message": "success",
      "data": []
    },
    {
      "image_path": "/mnt/d/.../img3.jpg",
      "code": -1,
      "message": "Failed to load image",
      "data": []
    }
  ]
}

```



### 3.3 视频推理 (Video Inference)

**POST** `/predict_video`

* **功能**: 处理视频文件，逐帧进行目标检测（批量优化，性能提升3-5倍）。
* **Request Body**:
```json
{
  "video_path": "/mnt/d/项目/05_API_Service/backend/temp_uploads/test.mp4",
  "output_path": "/mnt/d/项目/05_API_Service/backend/temp_uploads/test_output.mp4",
  "conf_threshold": 0.25,
  "model_type": "4060-v3-n-fp32"
}

```

* **核心优化**:
  - ✅ **批量推理**: 每次处理 8 帧，充分利用 GPU 并行能力
  - ✅ **内存流水线**: 全程在内存/显存中操作，不写入临时图片文件
  - ✅ **零硬盘IO**: 视频解码 → 批量推理 → 绘制框 → 编码输出，完全在内存完成
  - ⚡ **性能**: 1080p 视频可达 100-150 FPS 处理速度


* **Response**:
```json
{
  "code": 0,
  "message": "success",
  "model_used": "YOLOv11-Nodecode-FP32",
  "video_info": {
    "resolution": "1920x1080",
    "fps": 30.0,
    "total_frames": 900,
    "duration_seconds": 30.0
  },
  "processing": {
    "processed_frames": 900,
    "total_detections": 245,
    "processing_time_seconds": 8.5,
    "average_fps": 105.88
  },
  "output_path": "/mnt/d/.../test_output.mp4"
}

```



### 3.4 健康检查 (Health)

**GET** `/health`

* **功能**: 检查 C++ 服务是否存活。
* **Response**:
```json
{
  "status": "running", 
  "model": "YOLOv11-Nodecode", 
  "device": "CUDA:0"
}

```



---

## 4. 开发指南与工具 (Developer Guide)

### 4.1 [Python] 路径转换函数 (必须实现)

在 Python 端 (`utils/path_utils.py`) 必须包含此函数，用于在调用 C++ 前转换路径：

```python
import os

def convert_path_to_wsl(win_path: str) -> str:
    """
    Windows Path -> WSL Path
    Example: D:\data\img.jpg -> /mnt/d/data/img.jpg
    """
    abs_path = os.path.abspath(win_path) # 确保是绝对路径
    linux_path = abs_path.replace('\\', '/') # 替换反斜杠
    
    # 处理盘符 (C: -> /mnt/c)
    if ':' in linux_path:
        drive, tail = linux_path.split(':', 1)
        return f"/mnt/{drive.lower()}{tail}"
    return linux_path

```
### 4.2 [Python] 七牛云上传工具 (utils/oss_client.py)
4.1 环境准备
Python 依赖: `pip install qiniu flask requests ...`

七牛云配置: 注册账号 -> 创建对象存储空间 (Bucket) -> 获取 AccessKey/SecretKey。

4.2 [Python] 七牛云上传工具类 (utils/oss_client.py)
```python示例
from qiniu import Auth, put_file
import config

q = Auth(config.QINIU_AK, config.QINIU_SK)

def upload_file(local_path, key):
    """
    local_path: 本地文件绝对路径
    key: 上传到云端的文件名 (建议用 uuid)
    """
    token = q.upload_token(config.QINIU_BUCKET, key, 3600)
    ret, info = put_file(token, key, local_path)
    if info.status_code == 200:
        return f"{config.QINIU_DOMAIN}/{key}"
    return None
```
### 4.3 [C++] 启动配置

C++ 开发者需确保 `app_http.cpp` 中监听地址为通配地址，以便 Windows 宿主机连接：

```cpp
// 必须监听 0.0.0.0
svr.listen("0.0.0.0", 8080);

```

### 4.4 联调 Checklist

1. [ ] **图片存储**: 确认 Python 将图片存到了 Windows 的非系统盘（如 `D:/CourseProject/static/`）。
2. [ ] **网络连通**: Python 端尝试 `curl http://localhost:8080/health` 确认 C++ 服务存活。
3. [ ] **路径权限**: 确认 WSL 中能通过 `ls /mnt/d/...` 看到 Python 保存的图片。
4. [ ] **OSS配置**: 确保 config.py 里填了正确的 AK/SK 和域名。
5. [ ] **定期清理**: 建议写一个简单的定时任务，每天凌晨删除 temp_uploads 里超过 24 小时的图片，防止磁盘爆满（因为图片已经上了 OSS，本地可以删）。