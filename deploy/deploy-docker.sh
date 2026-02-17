#!/bin/bash
# Docker 部署脚本

set -e

echo "===== Docker 部署工单自动化系统 ====="

# 1. 检查 Docker 和 Docker Compose
echo "[1/3] 检查 Docker 环境..."
if ! command -v docker &> /dev/null; then
    echo "错误：未安装 Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "错误：未安装 Docker Compose"
    exit 1
fi

# 2. 检查 .env 文件
echo "[2/3] 检查环境变量配置..."
if [ ! -f ".env" ]; then
    echo "警告：未找到 .env 文件，复制 .env.example..."
    cp .env.example .env
    echo "请编辑 .env 文件，填入实际的配置信息"
    exit 1
fi

# 3. 构建并启动
echo "[3/3] 构建并启动容器..."
docker-compose build
docker-compose up -d

echo ""
echo "===== 部署完成 ====="
echo ""
echo "查看日志: docker-compose logs -f"
echo "停止服务: docker-compose down"
echo "重启服务: docker-compose restart"
