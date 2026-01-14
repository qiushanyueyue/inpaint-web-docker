#!/bin/bash
# Inpaint-Web Docker 一键更新脚本
# 在项目目录内运行: ./update.sh

set -e

echo "=============================================="
echo "🔄 Inpaint-Web Docker 更新脚本"
echo "=============================================="

# 拉取最新代码
echo ""
echo "📥 拉取最新代码..."
git pull origin main

# 停止现有容器
echo ""
echo "🛑 停止现有容器..."
docker compose -f docker-compose.gpu.yml down

# 重新构建并启动
echo ""
echo "🔨 重新构建并启动容器..."
docker compose -f docker-compose.gpu.yml up -d --build

# 等待服务启动
echo ""
echo "⏳ 等待服务启动..."
sleep 5

# 检查服务状态
echo ""
echo "📊 服务状态:"
docker compose -f docker-compose.gpu.yml ps

# 检查后端健康状态
echo ""
echo "🏥 检查后端健康状态..."
curl -s http://localhost:8888/api/health | python3 -m json.tool 2>/dev/null || echo "后端服务可能还在启动中..."

echo ""
echo "=============================================="
echo "✅ 更新完成！"
echo "   前端地址: http://localhost:3332"
echo "   后端地址: http://localhost:8888"
echo "=============================================="
