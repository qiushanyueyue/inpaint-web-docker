# Inpaint-Web Docker 部署指南

## 项目说明

这是 Inpaint-Web 项目的本地化 Docker 版本，已将 ONNX 模型文件集成到镜像中，**无需访问国际互联网即可使用**。

## 特性

✅ **完全离线运行** - 模型文件已打包在镜像中  
✅ **开箱即用** - 首次访问无需等待下载  
✅ **端口 3332** - 访问地址：`http://localhost:3332`  
✅ **生产优化** - 使用 Nginx 提供服务，支持 Gzip 压缩

## 快速开始

### 方式一：使用 Docker Compose（推荐）

```bash
# 克隆仓库
git clone https://github.com/lxfater/inpaint-web.git
cd inpaint-web

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

访问：`http://localhost:3332`

### 方式二：使用 Docker 命令

```bash
# 构建镜像
docker build -t inpaint-web .

# 运行容器
docker run -d -p 3332:3332 --name inpaint-web inpaint-web

# 查看日志
docker logs -f inpaint-web

# 停止容器
docker stop inpaint-web

# 删除容器
docker rm inpaint-web
```

## 模型文件说明

项目包含两个 ONNX 模型文件：

1. **Inpaint 模型** (`migan_pipeline_v2.onnx`) - 约 27MB
   - 用于图像修复功能
2. **Super-Resolution 模型** (`realesrgan-x4.onnx`) - 约 64MB
   - 用于图像超分辨率（高清化）功能

这些模型在 Docker 构建时自动下载并打包到镜像中。

## 技术架构

- **前端**: React + TypeScript + Vite
- **模型推理**: ONNX Runtime Web (WebGPU/WASM)
- **生产服务器**: Nginx
- **端口**: 3332

## 镜像大小

- 预计镜像大小：约 200-300MB
- 包含模型文件：约 91MB

## 自定义端口

如需修改端口，编辑 `docker-compose.yml`：

```yaml
ports:
  - 'YOUR_PORT:3332' # 将 YOUR_PORT 改为你想要的端口
```

或使用 Docker 命令：

```bash
docker run -d -p YOUR_PORT:3332 --name inpaint-web inpaint-web
```

## 故障排查

### 1. 端口已被占用

```bash
# 查看 3332 端口占用情况
lsof -i :3332

# 或更换其他端口
docker run -d -p 8080:3332 --name inpaint-web inpaint-web
```

### 2. 构建失败

```bash
# 清理 Docker 缓存
docker builder prune

# 重新构建
docker-compose build --no-cache
```

### 3. 查看容器日志

```bash
docker logs inpaint-web
```

## 开发模式

如需本地开发（非 Docker）：

```bash
# 安装依赖
npm install

# 下载模型文件
chmod +x download-models.sh
./download-models.sh

# 启动开发服务器
npm run start
```

访问：`http://localhost:5173`

## 浏览器要求

- **推荐**: Chrome/Edge 113+ (支持 WebGPU，性能最佳)
- **备选**: Firefox/Safari (使用 WASM，性能略低)

## 离线验证

断开网络连接后访问 `http://localhost:3332`，验证所有功能正常工作。

## 维护与更新

### 更新项目

当项目有新版本或修补程序时，按以下步骤更新：

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 重新构建镜像 (确保包含最新的代码和依赖)
# 普通版
docker-compose build --no-cache
# GPU 版
docker-compose -f docker-compose.gpu.yml build --no-cache

# 3. 重启服务
# 普通版
docker-compose up -d
# GPU 版
docker-compose -f docker-compose.gpu.yml up -d
```

### 清理空间

如果更新后产生未使用的镜像，可以运行：

```bash
docker image prune -f
```

## 许可证

遵循原项目许可证：GPL-3.0

## 相关链接

- 原项目：https://github.com/lxfater/inpaint-web
- 在线演示：https://inpaintweb.lxfater.com/
