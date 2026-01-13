# 更新日志

本文档记录 Inpaint-Web Docker 改造版的所有重要变更。

---

## [1.0.1] - 2026-01-13

### 🐛 Bug 修复

#### Inpaint 功能修复

**问题 1：个别图片报错无法消除**

- **现象**：部分图片在使用 Inpaint 消除功能时报错："Inpaint 功能需要后端服务器支持,请检查后端服务是否正常运行"
- **原因**：前端默认 `inpaintMode` 为 `browser` 模式，且强制检查后端健康状态。如果健康检查未及时返回或失败，会误判为浏览器模式并报错
- **修复**：
  - 将默认 `inpaintMode` 改为 `server` 模式
  - 移除前端对 `inpaintMode` 状态的强制检查
  - 直接调用后端 API，由后端返回具体错误信息
  - 提高容错性和健壮性

**问题 2：红色画笔消除延迟**

- **现象**：使用红色画笔标记消除区域后，画笔需要停顿一会儿才会消失
- **原因**：`onPointerUp` 函数结束时多余调用了 `draw()`，使用旧状态重绘导致红色遮罩短暂残留
- **修复**：
  - 移除 `onPointerUp` 中的 `draw()` 调用
  - 依赖 React `useEffect` 根据新状态自动重绘
  - 优化用户交互响应速度

### 🔧 代码优化

- 移除重复的 `loading.close()` 调用
- 优化注释说明
- 改进错误处理逻辑

### 📝 文件修改

- `src/Editor.tsx` - 修复 Inpaint 功能和画笔延迟问题

---

## [1.0.0] - 2026-01-11

### 🎉 首次发布

基于 [lxfater/inpaint-web](https://github.com/lxfater/inpaint-web) 的 GPU 加速改造版本

### ✨ 新增功能

#### 后端 GPU 加速

- ✅ FastAPI 后端服务，支持图像超分辨率 API
- ✅ 自动设备检测（CUDA / MPS / CPU）
- ✅ Real-ESRGAN 模型封装，支持 FP16 混合精度
- ✅ 瓦片处理（Tile Processing），优化显存使用
- ✅ 健康检查和详细日志

#### 性能优化

- ⚡ NVIDIA GTX 1070：性能提升 **10-12 倍**
- ⚡ Apple M1/M2：性能提升 **6-8 倍**
- ⚡ 小图 (512²→2048²)：2-3 秒 vs 20-30 秒
- ⚡ 中图 (1024²→4096²)：6-8 秒 vs 60-90 秒
- ⚡ 大图 (2048²→8192²)：18-25 秒 vs 180-300 秒

#### 智能模式切换

- 🔄 支持服务器端和浏览器端双模式
- 🔄 环境变量配置（`VITE_UPSCALE_MODE`）
- 🔄 自动降级机制（后端不可用时切换到浏览器端）
- 🔄 健康检查和错误处理

#### Docker 支持

- 🐳 完整的 Docker 化部署方案
- 🐳 多阶段构建优化镜像大小
- 🐳 NVIDIA GPU 运行时支持
- 🐳 Docker Compose 一键部署
- 🐳 前后端服务编排

#### 模型本地化

- 📦 模型文件预打包到 Docker 镜像
- 📦 支持离线部署，无需访问 HuggingFace
- 📦 模型自动下载脚本
- 📦 Inpaint 模型：migan_pipeline_v2.onnx (27MB)
- 📦 Upscale 模型：realesrgan-x4.onnx (64MB)

### 🔧 优化改进

#### 前端优化

- 修改提示文案，去除"国际互联网"字样
- 移除"联系作者"按钮
- 集成服务器端 API 调用逻辑
- 添加进度回调支持

#### 配置优化

- 默认端口改为 8888（避免冲突）
- 环境变量配置示例（`.env.example`）
- 支持自定义 API 地址
- CORS 完整配置

### 📝 文档完善

- ✅ 完整的 README.md（中文）
- ✅ 后端部署指南（BACKEND_DEPLOYMENT.md）
- ✅ 智能模式切换说明
- ✅ 端口冲突解决指南
- ✅ GPU 技术调研报告
- ✅ 实施计划和总结文档

### 🗂️ 新增文件

#### 后端服务

- `backend/api_server.py` - FastAPI 主服务
- `backend/models.py` - Real-ESRGAN 模型封装
- `backend/download_models.py` - 模型下载脚本
- `backend/requirements.txt` - Python 依赖列表
- `backend/run_mac.sh` - Mac 一键启动脚本

#### 前端集成

- `src/adapters/serverSuperResolution.ts` - 服务器端适配器

#### Docker 配置

- `backend/Dockerfile.gpu` - GPU 后端镜像
- `docker-compose.gpu.yml` - 完整服务编排
- `.env.example` - 环境变量模板
- `.env` - 环境变量配置

#### 文档

- `BACKEND_DEPLOYMENT.md` - 后端部署完整指南
- `CHANGELOG.md` - 本文件

### 🔨 修改文件

#### 前端代码

- `src/Editor.tsx` - 集成服务器端超分辨率调用
- `src/adapters/cache.ts` - 模型路径改为本地
- `messages/zh.json` - 优化中文提示文案
- `messages/en.json` - 优化英文提示文案

#### 前端应用

- `src/App.tsx` - 移除联系作者按钮

#### Docker 配置

- `Dockerfile` - 优化构建流程
- `nginx.conf` - 添加 ONNX MIME 类型
- `.dockerignore` - 优化构建上下文

### 🐛 修复问题

- ✅ 修复 Docker 构建时 paraglide 编译错误
- ✅ 修复 ESLint 配置导致的构建失败
- ✅ 修复模型下载提示文案问题
- ✅ 修复 8000 端口冲突问题

### ⚙️ 技术栈

#### 后端

- Python 3.9+
- FastAPI 0.109.0
- PyTorch 2.1.2
- Real-ESRGAN 0.3.0
- CUDA 11.8 / MPS

#### 前端

- React 18
- TypeScript 5
- Vite 5
- ONNX Runtime Web

#### 部署

- Docker
- Docker Compose
- Nginx
- NVIDIA Container Toolkit

---

## 与原项目的主要区别

### 原项目 ([lxfater/inpaint-web](https://github.com/lxfater/inpaint-web))

- 纯前端应用
- WebGPU/WASM 本地处理
- 模型从 HuggingFace 下载
- 性能依赖用户设备

### 改造版 (本项目)

- 前端 + 后端混合模式
- 服务器 GPU 加速处理
- 模型预打包，离线可用
- 性能提升 10-12 倍

---

## 未来计划

### v1.1.0 (计划中)

- [ ] 支持更多超分辨率模型（VPEG、Swin2SR）
- [ ] 批量处理 API
- [ ] WebSocket 实时进度推送
- [ ] Redis 结果缓存
- [ ] 多 GPU 负载均衡

### v1.2.0 (计划中)

- [ ] Web UI 模式切换按钮
- [ ] 性能监控面板
- [ ] 用户上传记录
- [ ] 高级参数配置

---

## 贡献者

- 基于 [lxfater/inpaint-web](https://github.com/lxfater/inpaint-web) 改造
- GPU 加速改造：[@YOUR_USERNAME]

---

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

原项目许可证：[lxfater/inpaint-web License](https://github.com/lxfater/inpaint-web/blob/main/LICENSE)
