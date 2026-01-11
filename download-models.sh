#!/bin/bash

# 下载 Inpaint-Web 所需的 ONNX 模型文件
# 这些模型将被打包到 Docker 镜像中，避免用户从国际互联网下载

set -e

MODELS_DIR="public/models"

# 创建模型目录
mkdir -p "$MODELS_DIR"

echo "========================================"
echo "开始下载 ONNX 模型文件..."
echo "========================================"

# 下载 Inpaint 模型 (migan_pipeline_v2.onnx)
INPAINT_MODEL_URL="https://huggingface.co/andraniksargsyan/migan/resolve/main/migan_pipeline_v2.onnx"
INPAINT_MODEL_FILE="$MODELS_DIR/migan_pipeline_v2.onnx"

if [ -f "$INPAINT_MODEL_FILE" ]; then
    echo "✓ Inpaint 模型已存在，跳过下载"
else
    echo "正在下载 Inpaint 模型..."
    curl -L -o "$INPAINT_MODEL_FILE" "$INPAINT_MODEL_URL"
    echo "✓ Inpaint 模型下载完成"
fi

# 下载 Super-Resolution 模型 (realesrgan-x4.onnx)
SR_MODEL_URL="https://huggingface.co/lxfater/inpaint-web/resolve/main/realesrgan-x4.onnx"
SR_MODEL_FILE="$MODELS_DIR/realesrgan-x4.onnx"

if [ -f "$SR_MODEL_FILE" ]; then
    echo "✓ Super-Resolution 模型已存在，跳过下载"
else
    echo "正在下载 Super-Resolution 模型..."
    curl -L -o "$SR_MODEL_FILE" "$SR_MODEL_URL"
    echo "✓ Super-Resolution 模型下载完成"
fi

echo "========================================"
echo "所有模型下载完成！"
echo "========================================"

# 显示文件信息
ls -lh "$MODELS_DIR"
