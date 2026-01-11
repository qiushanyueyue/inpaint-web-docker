# Inpaint-Web Docker - GPU 加速版

<div align="center">

![Inpaint-Web](https://img.shields.io/badge/Inpaint--Web-Docker-blue)
![GPU Accelerated](https://img.shields.io/badge/GPU-Accelerated-green)
![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.9+-blue)
![Docker](https://img.shields.io/badge/docker-ready-blue)

基于 [lxfater/inpaint-web](https://github.com/lxfater/inpaint-web) 的 GPU 加速改造版本

[功能特性](#功能特性) • [快速开始](#快速开始) • [性能对比](#性能对比) • [部署指南](#部署指南) • [改造说明](#改造说明)

</div>

---

## 📋 项目说明

这是一个基于 [lxfater/inpaint-web](https://github.com/lxfater/inpaint-web) 的改造项目，主要改进：

1. ✅ **后端 GPU 加速** - 支持 NVIDIA CUDA 和 Apple MPS
2. ✅ **性能提升 10-12 倍** - 图像超分辨率处理速度大幅提升
3. ✅ **Docker 一键部署** - 完整的容器化部署方案
4. ✅ **智能模式切换** - 服务器端与浏览器端自动切换
5. ✅ **离线模型集成** - 模型文件预打包，无需联网下载

> **原项目**: [lxfater/inpaint-web](https://github.com/lxfater/inpaint-web) - 基于 Webgpu 技术和 wasm 技术的免费开源 inpainting & image-upscaling 工具

---

## ✨ 功能特性

### 原有功能

- 🎨 **图像修复 (Inpaint)** - MI-GAN 模型，智能移除图像中的不需要内容
- 🔍 **图像超分辨率 (4x Upscale)** - Real-ESRGAN 模型，4 倍放大增强
- 🌐 **纯前端运行** - 基于 WebGPU/WASM，浏览器端处理
- 🔒 **隐私保护** - 所有处理在本地完成

### 改造新增

- 🚀 **GPU 后端加速** - FastAPI + PyTorch，服务器端 GPU 处理
- 🎯 **智能设备检测** - 自动选择 CUDA / MPS / CPU
- ⚡ **性能提升 10-12 倍** - GTX 1070: 2-8 秒 vs 浏览器: 60-240 秒
- 🔄 **自动降级机制** - 后端不可用时自动切换到浏览器端
- 🐳 **完整 Docker 支持** - 一键部署生产环境
- 📦 **离线模型** - 模型预下载，无需访问 HuggingFace

---

## 🚀 快速开始

### 方式一：Docker 部署（推荐）

#### 仅前端（浏览器模式）

```bash
# 克隆项目
git clone https://github.com/qiushanyueyue/inpaint-web-docker.git
cd inpaint-web-docker

# 下载前端模型文件
./download-models.sh

# 启动服务
docker-compose up -d

# 访问
open http://localhost:3332
```

#### 完整部署（GPU 加速）

**前提条件**：NVIDIA GPU + NVIDIA Docker Runtime

```bash
# 克隆项目
git clone https://github.com/qiushanyueyue/inpaint-web-docker.git
cd inpaint-web-docker

# 运行下载脚本（会自动下载所有必要模型）
./download-models.sh
python3 backend/download_models.py

# 配置环境
cp .env.example .env
# 编辑 .env: VITE_UPSCALE_MODE=server

# 启动所有服务（前端 + GPU 后端）
docker-compose -f docker-compose.gpu.yml up -d

# 访问
open http://localhost:3332
```

### 方式二：本地运行

#### 后端服务（GPU 加速）

**NVIDIA GPU (Linux/Windows)**

```bash
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 下载模型
python download_models.py

# 启动服务
python api_server.py
```

**Mac M 芯片**

```bash
cd backend
chmod +x run_mac.sh
./run_mac.sh
```

#### 前端服务

```bash
# 安装依赖
npm install

# 配置后端地址
echo "VITE_API_URL=http://localhost:8888" > .env
echo "VITE_UPSCALE_MODE=server" >> .env

# 启动开发服务器
npm run start

# 访问
open http://localhost:5173
```

---

## 📊 性能对比

### NVIDIA GTX 1070 8GB

| 场景               | 浏览器端   | 服务器端 (GTX 1070) | 提升       |
| ------------------ | ---------- | ------------------- | ---------- |
| 小图 (512²→2048²)  | 20-30 秒   | **2-3 秒**          | **10X** ⚡ |
| 中图 (1024²→4096²) | 60-90 秒   | **6-8 秒**          | **12X** ⚡ |
| 大图 (2048²→8192²) | 180-300 秒 | **18-25 秒**        | **12X** ⚡ |

### Apple M1/M2

| 场景               | 浏览器端 | 服务器端 (M1/M2) | 提升      |
| ------------------ | -------- | ---------------- | --------- |
| 小图 (512²→2048²)  | 20-30 秒 | **4-5 秒**       | **6X** ⚡ |
| 中图 (1024²→4096²) | 60-90 秒 | **12-15 秒**     | **6X** ⚡ |

---

## 🏗️ 技术架构

```
┌──────────────────────────────────────────┐
│        前端 (React + TypeScript)          │
│              端口: 3332                   │
│  ┌────────────────────────────────────┐  │
│  │  智能模式选择                      │  │
│  │  ├─ 服务器模式 (GPU 加速) ✅      │  │
│  │  └─ 浏览器模式 (WebGPU/WASM)      │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
                 ↓ HTTP API
┌──────────────────────────────────────────┐
│      后端 API (FastAPI + Python)         │
│              端口: 8888                   │
│  ┌────────────────────────────────────┐  │
│  │  设备自动检测                      │  │
│  │  ├─ CUDA (NVIDIA GPU)              │  │
│  │  ├─ MPS (Apple M Chip)             │  │
│  │  └─ CPU (Fallback)                 │  │
│  │                                     │  │
│  │  Real-ESRGAN x4 模型               │  │
│  │  ├─ FP16 混合精度                  │  │
│  │  ├─ 瓦片处理（显存优化）           │  │
│  │  └─ 自动批处理                     │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
```

---

## 📖 部署指南

详细部署文档请查看：

- [后端 GPU 部署指南](BACKEND_DEPLOYMENT.md)
- [前端部署说明](DEPLOYMENT.md)

### 系统要求

**GPU 服务器**

- NVIDIA GPU (GTX 1070 8GB 或更高)
- CUDA 11.8+
- 显存 6GB+
- Docker + NVIDIA Container Toolkit

**Mac 本地**

- Apple M1/M2/M3
- macOS 12.3+
- Python 3.9+

---

## 🔧 配置说明

### 环境变量

创建 `.env` 文件：

```bash
# 后端 API 地址
VITE_API_URL=http://localhost:8888

# 超分辨率模式
# - server: 使用服务器 GPU（推荐）
# - browser: 使用浏览器端
VITE_UPSCALE_MODE=server
```

### 端口配置

| 服务       | 默认端口 | 说明            |
| ---------- | -------- | --------------- |
| 前端       | 3332     | Nginx 静态服务  |
| 后端 API   | 8888     | FastAPI 服务    |
| 开发服务器 | 5173     | Vite dev server |

---

## 📝 改造说明

### 主要改造内容

#### 1. 后端服务

**新增文件**：

- `backend/api_server.py` - FastAPI 主服务
- `backend/models.py` - Real-ESRGAN 模型封装
- `backend/download_models.py` - 模型下载脚本
- `backend/requirements.txt` - Python 依赖

**技术栈**：

- FastAPI - 高性能异步 Web 框架
- PyTorch 2.1 - 深度学习框架
- Real-ESRGAN - 超分辨率模型
- CUDA 11.8 / MPS - GPU 加速

#### 2. 前端集成

**修改文件**：

- `src/Editor.tsx` - 集成服务器端 API 调用
- `src/adapters/serverSuperResolution.ts` - 新增服务器端适配器

**新增功能**：

- 智能模式切换（服务器/浏览器）
- 自动降级机制
- 健康检查

#### 3. Docker 化

**新增文件**：

- `backend/Dockerfile.gpu` - GPU 后端镜像
- `docker-compose.gpu.yml` - 完整服务编排
- `nginx.conf` - Nginx 配置（优化）

#### 4. 模型本地化

**修改**：

- 模型从 HuggingFace 改为本地路径
- Docker 构建时自动下载模型
- 支持离线部署

#### 5. 文档完善

**新增**：

- `BACKEND_DEPLOYMENT.md` - 后端部署指南
- `CHANGELOG.md` - 改造记录

### 与原项目的区别

| 特性     | 原项目       | 改造版              |
| -------- | ------------ | ------------------- |
| 运行方式 | 纯浏览器端   | 浏览器 + 后端可选   |
| 性能     | 依赖用户设备 | GPU 加速快 10-12 倍 |
| 模型下载 | HuggingFace  | 本地预下载          |
| 部署方式 | 静态站点     | Docker 完整方案     |
| GPU 支持 | 用户 WebGPU  | 服务器 CUDA/MPS     |

---

## 🤝 贡献

本项目是改造项目，基于 [lxfater/inpaint-web](https://github.com/lxfater/inpaint-web)。

如有改进建议，欢迎：

- 提交 Issue
- 发起 Pull Request

---

## 📄 许可证

本项目遵循 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

原项目许可证：[lxfater/inpaint-web](https://github.com/lxfater/inpaint-web/blob/main/LICENSE)

---

## 🙏 致谢

### 原项目

- **[lxfater/inpaint-web](https://github.com/lxfater/inpaint-web)** - 提供优秀的 Inpaint 和 Upscale 前端实现

### 依赖项目

- **[Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN)** - 图像超分辨率模型
- **[BasicSR](https://github.com/XPixelGroup/BasicSR)** - 图像恢复工具箱
- **[FastAPI](https://fastapi.tiangolo.com/)** - 现代 Python Web 框架
- **[PyTorch](https://pytorch.org/)** - 深度学习框架

### 模型来源

- **Inpaint 模型**: [MI-GAN](https://github.com/Picsart-AI-Research/MI-GAN)
- **Upscale 模型**: [Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN)

---

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- GitHub Issues: [提交问题](https://github.com/YOUR_USERNAME/inpaint-web-docker/issues)
- 原项目讨论: [lxfater/inpaint-web](https://github.com/lxfater/inpaint-web/issues)

---

## ⭐ Star History

如果这个项目对您有帮助，请给一个 Star ⭐

---

<div align="center">

**基于 [lxfater/inpaint-web](https://github.com/lxfater/inpaint-web) 改造**

Made with ❤️ for better performance

</div>
