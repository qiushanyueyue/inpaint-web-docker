#!/bin/bash

# Mac M 芯片运行脚本
# 自动安装依赖并启动后端服务

set -e

echo "========================================"
echo "Inpaint-Web 后端服务 (Mac M 芯片)"
echo "========================================"

# 检查 Python 版本
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python 版本: $python_version"

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "安装 Python 依赖..."
pip install --upgrade pip
pip install -r requirements.txt

# 下载模型（如果不存在）
if [ ! -f "models/RealESRGAN_x4plus.pth" ]; then
    echo "下载模型文件..."
    python download_models.py
fi

# 检测 MPS 可用性
python3 << EOF
import torch
if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
    print("✓ MPS (Metal Performance Shaders) 可用")
    print(f"  PyTorch 版本: {torch.__version__}")
else:
    print("⚠️  MPS 不可用，将使用 CPU")
EOF

echo "========================================"
echo "启动后端服务..."
echo "========================================"

# 启动服务
python api_server.py
