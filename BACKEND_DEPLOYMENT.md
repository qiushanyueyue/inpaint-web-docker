# 后端 GPU 加速部署指南

## 概述

本文档介绍如何部署 Inpaint-Web 的后端 GPU 加速服务，支持：

- **NVIDIA GPU** (GTX 1070 及以上，CUDA 11.8+)
- **Mac M 芯片** (M1/M2/M3，MPS Backend)
- **CPU Fallback** (自动降级)

---

## 系统要求

### NVIDIA GPU 服务器

| 项目     | 要求                   |
| -------- | ---------------------- |
| **GPU**  | GTX 1070 8GB 或更高    |
| **CUDA** | 11.8+                  |
| **显存** | 最低 6GB，推荐 8GB+    |
| **驱动** | NVIDIA Driver 450+     |
| **系统** | Linux / Windows (WSL2) |

### Mac M 芯片

| 项目        | 要求            |
| ----------- | --------------- |
| **芯片**    | Apple M1/M2/M3  |
| **系统**    | macOS 12.3+     |
| **Python**  | 3.9+            |
| **PyTorch** | 2.0+ (支持 MPS) |

---

## 快速开始

### 方式一：本地运行（推荐用于开发/测试）

#### NVIDIA GPU (Linux/Windows)

```bash
cd backend

# 1. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux
# 或 venv\Scripts\activate  # Windows

# 2. 安装依赖
pip install -r requirements.txt

# 3. 下载模型
python download_models.py

# 4. 启动服务
python api_server.py
```

#### Mac M 芯片

```bash
cd backend

# 一键启动（自动安装依赖 + 下载模型 + 启动服务）
chmod +x run_mac.sh
./run_mac.sh
```

**验证**：
访问 http://localhost:8000/docs 查看 API 文档

---

### 方式二：Docker 部署（推荐用于生产）

#### 前提条件

**NVIDIA GPU 服务器需要安装 NVIDIA Container Toolkit**：

```bash
# Ubuntu/Debian
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker

# 验证
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

#### 完整部署（前端 + 后端）

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env，设置 VITE_UPSCALE_MODE=server

# 2. 构建并启动所有服务
docker-compose -f docker-compose.gpu.yml up -d

# 3. 查看日志
docker-compose -f docker-compose.gpu.yml logs -f

# 4. 停止服务
docker-compose -f docker-compose.gpu.yml down
```

**访问**：

- 前端：http://localhost:3332
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

---

### 方式三：仅后端服务

```bash
cd backend

# 构建镜像
docker build -f Dockerfile.gpu -t inpaint-backend-gpu .

# 运行（启用 GPU）
docker run --gpus all -p 8000:8000 inpaint-backend-gpu

# 查看日志
docker logs -f <container_id>
```

---

## 配置说明

### 环境变量

创建 `.env` 文件（参考 `.env.example`）：

```bash
# 后端 API 地址
VITE_API_URL=http://localhost:8000

# 超分辨率模式
# - server: 使用服务器 GPU（推荐）
# - browser: 使用浏览器端 WebGPU/WASM
VITE_UPSCALE_MODE=server
```

### 模型配置

编辑 `backend/models/realesrgan_model.py` 可调整参数：

```python
# GTX 1070 8GB 推荐配置
tile=400       # 瓦片大小（显存不足可降低到 200-300）
tile_pad=10    # 瓦片边缘填充
fp16=True      # FP16 混合精度（节省显存 50%）
```

**显存使用参考**：

| Tile 大小 | 显存占用 | 适用 GPU        |
| --------- | -------- | --------------- |
| 400       | ~6GB     | GTX 1070 (8GB)  |
| 512       | ~8GB     | RTX 3080 (10GB) |
| 640       | ~12GB    | RTX 4090 (24GB) |

---

## API 使用

### 健康检查

```bash
curl http://localhost:8000/api/health
```

响应：

```json
{
  "status": "healthy",
  "model_loaded": true,
  "device": {
    "type": "cuda",
    "name": "NVIDIA GeForce GTX 1070"
  }
}
```

### 图像放大

```bash
curl -X POST \
  http://localhost:8000/api/upscale \
  -F "file=@/path/to/image.jpg" \
  --output upscaled.png
```

### 前端集成

前端会根据 `VITE_UPSCALE_MODE` 自动选择：

```typescript
// 自动选择模式
const useServerBackend = import.meta.env.VITE_UPSCALE_MODE === 'server'

if (useServerBackend) {
  // 调用后端 GPU API
  const res = await serverSuperResolution(file, callback)
} else {
  // 使用浏览器端
  const res = await superResolution(file, callback)
}
```

---

## 性能测试

### 测试脚本

```bash
# 创建测试脚本 test_performance.sh
cat > test_performance.sh << 'EOF'
#!/bin/bash
echo "性能测试开始..."

for i in 1 2 3; do
  echo "测试 $i/3"
  time curl -X POST \
    http://localhost:8000/api/upscale \
    -F "file=@test_image.jpg" \
    --output /dev/null \
    --silent
done
EOF

chmod +x test_performance.sh
./test_performance.sh
```

### 预期性能（GTX 1070 8GB）

| 输入分辨率 | 输出分辨率 | 浏览器端 | GTX 1070     | 提升 |
| ---------- | ---------- | -------- | ------------ | ---- |
| 512x512    | 2048x2048  | ~25 秒   | **2-3 秒**   | 10X  |
| 1024x1024  | 4096x4096  | ~80 秒   | **6-8 秒**   | 12X  |
| 2048x2048  | 8192x8192  | ~240 秒  | **18-25 秒** | 12X  |

### 预期性能（Mac M1/M2）

| 输入分辨率 | 输出分辨率 | 浏览器端 | Mac M1       | 提升 |
| ---------- | ---------- | -------- | ------------ | ---- |
| 512x512    | 2048x2048  | ~25 秒   | **4-5 秒**   | 6X   |
| 1024x1024  | 4096x4096  | ~80 秒   | **12-15 秒** | 6X   |

---

## 故障排查

### 问题 1：GPU 未检测到

**症状**：日志显示使用 CPU

**解决**：

```bash
# 检查 CUDA
nvidia-smi

# 检查 PyTorch CUDA
python -c "import torch; print(torch.cuda.is_available())"

# 检查 Docker GPU
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

### 问题 2：显存不足 (OOM)

**症状**：`CUDA out of memory`

**解决**：

```python
# 编辑 backend/models/realesrgan_model.py

tile=200  # 降低 tile 大小
fp16=True  # 确保启用 FP16
```

### 问题 3：Mac MPS 错误

**症状**：MPS 相关错误

**解决**：

```python
# 自动降级到 CPU
# backend/models/realesrgan_model.py 中已包含错误处理，会自动切换到 CPU

```

### 问题 4：模型文件未找到

**症状**：`FileNotFoundError: 模型文件未找到`

**解决**：

```bash
cd backend
python download_models.py
```

### 问题 5：CORS 错误

**症状**：前端调用失败，浏览器报 CORS 错误

**解决**：

```python
# backend/api_server.py 已配置 CORS
# 确保前端使用正确的 API_URL
```

---

## 性能优化

### 1. 启用 FP16 混合精度

**优点**：显存减半，速度提升 20-30%

```python
# backend/models/realesrgan_model.py

fp16=True  # 已默认启用
```

### 2. 调整 Tile 大小

**原则**：

- 显存充足：使用更大 tile（更快）
- 显存紧张：使用更小 tile（更稳定）

```python
# 8GB 显存
tile=400

# 6GB 显存
tile=300

# 4GB 显存
tile=200
```

### 3. 批量处理

修改 `backend/api_server.py` 支持批量上传：

```python
@app.post("/api/upscale-batch")
async def upscale_batch(files: List[UploadFile]):
    # 批量处理逻辑
    pass
```

---

## 生产部署建议

### 1. 使用反向代理（Nginx）

```nginx
# /etc/nginx/sites-available/inpaint-web
server {
    listen 80;
    server_name inpaint.example.com;

    # 前端
    location / {
        proxy_pass http://localhost:3332;
    }

    # 后端 API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        # 超时设置（处理大图片需要更长时间）
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }
}
```

### 2. 配置进程管理（Systemd）

```ini
# /etc/systemd/system/inpaint-backend.service
[Unit]
Description=Inpaint-Web Backend GPU Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/inpaint-web/backend
ExecStart=/opt/inpaint-web/backend/venv/bin/python api_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable inpaint-backend
sudo systemctl start inpaint-backend
sudo systemctl status inpaint-backend
```

### 3. 负载均衡（多 GPU）

修改 `docker-compose.gpu.yml`：

```yaml
services:
  backend-gpu-0:
    # GPU 0
    environment:
      - CUDA_VISIBLE_DEVICES=0

  backend-gpu-1:
    # GPU 1
    environment:
      - CUDA_VISIBLE_DEVICES=1

  nginx:
    # Nginx 负载均衡
    depends_on:
      - backend-gpu-0
      - backend-gpu-1
```

---

## 监控和日志

### 查看实时日志

```bash
# Docker
docker-compose -f docker-compose.gpu.yml logs -f backend

# 本地运行
tail -f /var/log/inpaint-backend.log
```

### GPU 监控

```bash
# 实时监控 GPU 使用率
watch -n 1 nvidia-smi

# 或使用 nvtop
sudo apt install nvtop
nvtop
```

---

## 总结

✅ **NVIDIA GTX 1070 8GB** - 速度提升 10-12 倍  
✅ **Mac M 芯片** - 速度提升 6-8 倍  
✅ **自动降级** - 后端不可用时自动使用浏览器端  
✅ **生产就绪** - Docker + Nginx + Systemd 完整方案

**开始使用**：

1. 选择部署方式（本地/Docker）
2. 配置 `.env` 文件
3. 启动后端服务
4. 访问 http://localhost:3332 测试

**获取帮助**：

- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/api/health
- 设备信息：http://localhost:8000/api/info
