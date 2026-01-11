#!/bin/bash

# GitHub 仓库发布脚本
# 自动创建并推送到 GitHub

set -e

echo "=========================================="
echo "GitHub 仓库发布助手"
echo "=========================================="
echo ""

# 检查是否已提交
if ! git log -1 &>/dev/null; then
    echo "❌ 错误: 没有找到 Git 提交"
    echo "请先运行: git commit"
    exit 1
fi

# 获取用户名
echo "请输入您的 GitHub 用户名:"
read -p "用户名: " GITHUB_USERNAME

if [ -z "$GITHUB_USERNAME" ]; then
    echo "❌ 用户名不能为空"
    exit 1
fi

REPO_NAME="inpaint-web-docker"

echo ""
echo "=========================================="
echo "准备发布到:"
echo "https://github.com/$GITHUB_USERNAME/$REPO_NAME"
echo "=========================================="
echo ""

# 检查是否安装了 gh (GitHub CLI)
if command -v gh &> /dev/null; then
    echo "✓ 检测到 GitHub CLI"
    echo ""
    echo "选择创建方式:"
    echo "1) 使用 GitHub CLI 自动创建仓库 (推荐)"
    echo "2) 手动创建仓库"
    read -p "请选择 (1/2): " choice
    
    if [ "$choice" = "1" ]; then
        echo ""
        echo "🚀 使用 GitHub CLI 创建仓库..."
        
        # 创建仓库
        gh repo create "$REPO_NAME" \
            --public \
            --description "Inpaint-Web GPU 加速改造版 - 基于 lxfater/inpaint-web" \
            --source=. \
            --remote=origin \
            --push
        
        echo ""
        echo "✅ 发布完成!"
        echo "仓库地址: https://github.com/$GITHUB_USERNAME/$REPO_NAME"
        exit 0
    fi
fi

# 手动创建流程
echo ""
echo "📝 请按以下步骤操作:"
echo ""
echo "1. 访问 https://github.com/new"
echo "2. 仓库名称: $REPO_NAME"
echo "3. 描述: Inpaint-Web GPU 加速改造版 - 基于 lxfater/inpaint-web"
echo "4. 可见性: Public"
echo "5. ❌ 不要勾选 'Initialize this repository with:' 下的任何选项"
echo "6. 点击 'Create repository'"
echo ""
read -p "完成创建后按回车继续..."

# 添加远程仓库
echo ""
echo "🔗 添加远程仓库..."
git remote remove origin 2>/dev/null || true
git remote add origin "https://github.com/$GITHUB_USERNAME/$REPO_NAME.git"

# 推送
echo ""
echo "📤 推送代码到 GitHub..."
git branch -M main
git push -u origin main

echo ""
echo "=========================================="
echo "✅ 发布成功!"
echo "=========================================="
echo ""
echo "仓库地址: https://github.com/$GITHUB_USERNAME/$REPO_NAME"
echo ""
echo "下一步:"
echo "1. 访问仓库添加 Topics 标签"
echo "2. 创建 Release v1.0.0"
echo "3. 添加项目截图"
echo ""
