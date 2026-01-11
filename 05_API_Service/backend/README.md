# Python 后端项目说明文档

## 📋 项目简介

这是基于 Flask 的电力巡检系统后端 API 服务，采用微服务架构，分离业务层和计算层。

### 系统架构
- **业务层 (Python/Flask)**: 运行在 Windows，负责用户交互、数据库、文件存储
- **计算层 (C++/TensorRT)**: 运行在 WSL (Ubuntu)，负责高性能 AI 推理
- **存储层**: 本地 D 盘缓存 + 七牛云 OSS 持久化

---

## 🚀 快速开始

### 1. 环境要求
- Python 3.8+
- MySQL 5.7+ 或 MariaDB
- 七牛云账号 (用于 OSS 存储)
- C++ 推理服务 (运行在 WSL)

### 2. 激活 Conda 环境并安装依赖

项目使用 conda 环境 `electric_inspection`，请按以下步骤操作：

```bash
# 激活 conda 环境
conda activate electric_inspection

# 进入后端目录
cd 05_API_Service\backend

# 安装依赖
pip install -r requirements.txt
```

**提示**: 如果你还没有创建这个环境，可以先创建：
```bash
conda create -n electric_inspection python=3.9 -y
conda activate electric_inspection
```

### 3. 配置环境变量

复制 `.env.example` 为 `.env` 并填写实际配置:

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置数据库、七牛云等信息。

### 4. 初始化数据库

```bash
# 创建数据库
mysql -u root -p
CREATE DATABASE electric_inspection CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;

# 自动创建表 (首次运行时会自动执行)
python app.py
```

### 5. 启动服务

```bash
python app.py
```

服务将在 `http://0.0.0.0:5000` 启动。

---

## 📁 项目结构

```
backend/
├── app.py                # 应用主入口
├── config.py             # 配置文件
├── requirements.txt      # 依赖包
├── .env                  # 环境变量 (需自行创建)
├── temp_uploads/         # 临时上传目录
├── api/                  # API 路由模块
│   ├── auth.py          # 认证接口
│   ├── detect.py        # 推理接口
│   ├── records.py       # 历史记录接口
│   └── stats.py         # 统计接口
├── models/              # 数据库模型
│   ├── user.py          # 用户模型
│   └── record.py        # 检测记录模型
└── utils/               # 工具类
    ├── path_utils.py    # 路径转换
    ├── cpp_client.py    # C++ 服务客户端
    ├── oss_client.py    # 七牛云上传
    └── image_proc.py    # 图像处理
```

---

## 🔌 API 接口

Base URL: `http://<server_ip>:5000/api/v1`

### 认证模块 `/auth`
- `POST /auth/login` - 用户登录
- `GET /auth/verify` - 验证 Token
- `POST /auth/change_password` - 修改密码

### 推理模块 `/detect`
- `POST /detect/image` - 上传并检测图片
- `GET /detect/health` - C++ 服务健康检查

### 历史记录 `/records`
- `GET /records/list` - 获取记录列表 (分页+筛选)
- `GET /records/detail/<id>` - 获取记录详情
- `DELETE /records/delete/<id>` - 删除记录

### 统计模块 `/stats`
- `GET /stats/dashboard` - 仪表盘数据
- `GET /stats/monthly` - 月度统计

详细接口文档请参考 `api_design.md`。

---

## 🔧 配置说明

### config.py 关键配置

```python
# 数据库
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://user:pass@host:port/db'

# C++ 服务
CPP_SERVICE_URL = 'http://localhost:8080'

# 七牛云
QINIU_ACCESS_KEY = 'your-ak'
QINIU_SECRET_KEY = 'your-sk'
QINIU_BUCKET_NAME = 'your-bucket'
QINIU_DOMAIN = 'http://your-cdn-domain.com'

# 类别标签 (根据你的模型调整)
CLASS_LABELS = {
    0: 'insulator_broken',
    1: 'nest',
    2: 'ring_shifted',
}
```

---

## 🧪 测试

### 测试登录
```bash
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

### 测试检测 (需要 Token)
```bash
curl -X POST http://localhost:5000/api/v1/detect/image \
  -H "Authorization: Bearer <your-token>" \
  -F "file=@test.jpg"
```

---

## ⚠️ 注意事项

1. **路径问题**: 图片必须存储在非系统盘 (D:/ 或 E:/)
2. **C++ 服务**: 确保 WSL 中的 C++ 服务已启动并监听 8080 端口
3. **七牛云**: 配置正确的 AK/SK 和 Bucket 名称
4. **默认账号**: admin / admin123 (首次运行自动创建)
5. **生产环境**: 修改 SECRET_KEY、JWT_SECRET_KEY 等敏感配置

---

## 📝 常见问题

**Q: 如何修改默认端口?**  
A: 在 `app.py` 的 `app.run()` 中修改 `port` 参数。

**Q: 数据库连接失败?**  
A: 检查 MySQL 是否运行，以及 `.env` 中的数据库配置是否正确。

**Q: C++ 服务无法连接?**  
A: 确保 WSL 中的 C++ 服务已启动，使用 `curl http://localhost:8080/health` 测试。

**Q: 图片上传失败?**  
A: 检查 `temp_uploads/` 目录权限，确保 Python 进程有写入权限。

---

## 📞 技术支持

如有问题，请查看 `api_design.md` 文档或联系开发团队。
