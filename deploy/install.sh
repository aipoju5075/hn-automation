#!/bin/bash
# 工单自动化系统部署脚本

set -e

APP_NAME="workorder-automation"
APP_DIR="/opt/${APP_NAME}"
SERVICE_FILE="/etc/systemd/system/${APP_NAME}.service"
USER_NAME="workorder"

echo "===== 开始部署工单自动化系统 ====="

# 1. 创建用户
echo "[1/7] 创建运行用户..."
if ! id "$USER_NAME" &>/dev/null; then
    sudo useradd -r -s /bin/false -d "$APP_DIR" "$USER_NAME"
    echo "用户 $USER_NAME 创建成功"
else
    echo "用户 $USER_NAME 已存在"
fi

# 2. 创建目录
echo "[2/7] 创建应用目录..."
sudo mkdir -p "$APP_DIR"
sudo mkdir -p "$APP_DIR/logs"
sudo mkdir -p "$APP_DIR/data/cookies"
sudo mkdir -p "$APP_DIR/data/files"
sudo mkdir -p "$APP_DIR/config"

# 3. 复制项目文件
echo "[3/7] 复制项目文件..."
# 假设在项目根目录执行
sudo cp -r src "$APP_DIR/"
sudo cp main.py "$APP_DIR/"
sudo cp requirements.txt "$APP_DIR/"
sudo cp -r config "$APP_DIR/"

# 4. 创建虚拟环境
echo "[4/7] 创建 Python 虚拟环境..."
cd "$APP_DIR"
sudo python3 -m venv venv
sudo "$APP_DIR/venv/bin/pip" install --upgrade pip
sudo "$APP_DIR/venv/bin/pip" install -r requirements.txt

# 5. 配置环境变量
echo "[5/7] 配置环境变量..."
if [ ! -f "$APP_DIR/.env" ]; then
    sudo cp .env.example "$APP_DIR/.env"
    echo "请编辑 $APP_DIR/.env 文件，填入实际的配置信息"
fi

# 6. 设置权限
echo "[6/7] 设置文件权限..."
sudo chown -R "$USER_NAME:$USER_NAME" "$APP_DIR"
sudo chmod 600 "$APP_DIR/.env"

# 7. 配置 Systemd 服务
echo "[7/7] 配置 Systemd 服务..."
sudo cp "deploy/${APP_NAME}.service" "$SERVICE_FILE"
sudo systemctl daemon-reload
sudo systemctl enable "$APP_NAME"

echo ""
echo "===== 部署完成 ====="
echo ""
echo "使用方法："
echo "  启动服务: sudo systemctl start $APP_NAME"
echo "  停止服务: sudo systemctl stop $APP_NAME"
echo "  查看状态: sudo systemctl status $APP_NAME"
echo "  查看日志: sudo journalctl -u $APP_NAME -f"
echo ""
echo "注意：请先编辑 $APP_DIR/.env 文件配置好环境变量后再启动服务"
