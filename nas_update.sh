#!/bin/bash
# NAS 更新脚本 - OpenCV Inpaint 方案

echo "🚀 开始更新 Inpaint-Web (OpenCV 方案)..."
echo ""

# 进入项目目录
cd /vol2/1000/docker2/inpaint-web-docker/inpaint-web-docker || exit 1

# 拉取最新代码
echo "📥 拉取最新代码..."
git pull origin main

# 停止现有服务
echo "🛑 停止现有服务..."
docker compose -f docker-compose.gpu.yml down

# 重新构建并启动
echo "🔨 重新构建并启动服务..."
docker compose -f docker-compose.gpu.yml up -d --build

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 查看服务状态
echo ""
echo "📊 服务状态:"
docker compose -f docker-compose.gpu.yml ps

# 查看后端日志
echo ""
echo "📋 后端日志 (最后 20 行):"
docker compose -f docker-compose.gpu.yml logs --tail=20 backend

echo ""
echo "✅ 更新完成!"
echo "🌐 访问: https://inpaint.yytianjin.online/"
