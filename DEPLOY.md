# 工单自动化系统部署指南

## 目录
- [方案一：Docker 部署（推荐）](#方案一docker-部署推荐)
- [方案二：Systemd 服务部署](#方案二systemd-服务部署)
- [方案三：Supervisor 部署](#方案三supervisor-部署)
- [服务器要求](#服务器要求)
- [常见问题](#常见问题)

---

## 服务器要求

### 最低配置
- **CPU**: 1 核
- **内存**: 512 MB
- **磁盘**: 5 GB
- **系统**: Linux (Ubuntu 20.04+/CentOS 7+) 或 Windows Server
- **Python**: 3.9+ (非 Docker 方案)

### 网络要求
- 可访问以下系统：
  - 工单系统: `https://gd.anyserves56.com`
  - ASD系统: `https://www.anyserves56.com`
  - 大物流系统: `https://www.anyserves56.com`
- 可访问 PushPlus API: `http://www.pushplus.plus`

---

## 方案一：Docker 部署（推荐）

### 前置条件
- 已安装 Docker 和 Docker Compose
```bash
# Ubuntu 安装 Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```

### 部署步骤

1. **上传项目到服务器**
```bash
# 使用 git 克隆或上传压缩包
git clone <你的仓库地址> /opt/workorder-automation
cd /opt/workorder-automation
```

2. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，填入所有配置
nano .env
```

3. **启动服务**
```bash
# 赋予执行权限并运行部署脚本
chmod +x deploy/deploy-docker.sh
./deploy/deploy-docker.sh

# 或手动执行：
docker-compose up -d
```

4. **查看日志**
```bash
docker-compose logs -f
```

### 常用命令
```bash
# 查看运行状态
docker-compose ps

# 重启服务
docker-compose restart

# 停止服务
docker-compose down

# 查看日志（最近 100 行）
docker-compose logs --tail=100

# 进入容器调试
docker-compose exec workorder-automation bash
```

---

## 方案二：Systemd 服务部署

### 前置条件
- Python 3.9+
- pip
- systemd

### 部署步骤

1. **上传项目到服务器**
```bash
# 上传项目文件到 /opt/workorder-automation
sudo mkdir -p /opt/workorder-automation
```

2. **运行安装脚本**
```bash
cd /opt/workorder-automation
sudo chmod +x deploy/install.sh
sudo ./deploy/install.sh
```

3. **配置环境变量**
```bash
sudo nano /opt/workorder-automation/.env
# 填入所有配置
```

4. **启动服务**
```bash
sudo systemctl start workorder-automation
```

### 常用命令
```bash
# 启动服务
sudo systemctl start workorder-automation

# 停止服务
sudo systemctl stop workorder-automation

# 重启服务
sudo systemctl restart workorder-automation

# 查看状态
sudo systemctl status workorder-automation

# 查看日志
sudo journalctl -u workorder-automation -f

# 查看历史日志
sudo journalctl -u workorder-automation --since "2024-01-01" --until "2024-01-31"
```

---

## 方案三：Supervisor 部署

适合：已有 Supervisor 环境，或需要 Web 管理界面

### 安装 Supervisor
```bash
# Ubuntu/Debian
sudo apt-get install supervisor

# CentOS/RHEL
sudo yum install supervisor
```

### 配置
创建配置文件 `/etc/supervisor/conf.d/workorder-automation.conf`：

```ini
[program:workorder-automation]
command=/opt/workorder-automation/venv/bin/python main.py
directory=/opt/workorder-automation
user=workorder
autostart=true
autorestart=true
startretries=3
stderr_logfile=/var/log/workorder-automation.err.log
stdout_logfile=/var/log/workorder-automation.out.log
environment=PYTHONUNBUFFERED="1"
```

### 启动
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start workorder-automation

# 查看状态
sudo supervisorctl status
```

---

## 环境变量配置

部署前必须配置 `.env` 文件：

```bash
# 工单系统配置
WORKORDER_USERNAME=你的用户名
WORKORDER_PASSWORD=你的密码

# ASD家电系统配置
ASD_USERNAME=你的用户名
ASD_PASSWORD=你的密码

# 大物流系统配置
LOGISTICS_USERNAME=你的用户名
LOGISTICS_PASSWORD=你的密码

# 自提人员名单
SELF_PICKUP_STAFF=陈起,陈双强,黄道章,李亮,王运孝,谢小习,陈海亮,唐殿岳

# 百度OCR配置（用于验证码识别）
BAIDU_OCR_API_KEY=你的API_KEY
BAIDU_OCR_SECRET_KEY=你的SECRET_KEY

# PushPlus 通知配置
PUSHPLUS_TOKEN=你的token
PUSHPLUS_ENABLED=true
```

---

## 常见问题

### Q1: 如何更新代码？

**Docker 方案：**
```bash
cd /opt/workorder-automation
git pull
docker-compose build
docker-compose up -d
```

**Systemd 方案：**
```bash
cd /opt/workorder-automation
git pull
sudo systemctl restart workorder-automation
```

### Q2: 日志文件在哪里？

**Docker:**
- 日志在容器内 `/app/logs/`，同时输出到 `docker-compose logs`
- 宿主机可通过 `docker-compose logs` 查看

**Systemd:**
- 应用日志：`/opt/workorder-automation/logs/app.log`
- 系统日志：`journalctl -u workorder-automation`

### Q3: 如何备份数据？

```bash
# 备份数据目录
tar -czf backup-$(date +%Y%m%d).tar.gz /opt/workorder-automation/data /opt/workorder-automation/logs

# 定时备份（添加到 crontab）
0 2 * * * tar -czf /backup/workorder-$(date +\%Y\%m\%d).tar.gz /opt/workorder-automation/data /opt/workorder-automation/logs
```

### Q4: 容器时间不对怎么办？

Docker Compose 已配置 `TZ=Asia/Shanghai`，如需修改：
```bash
# 进入容器
docker-compose exec workorder-automation bash

# 查看时间
date
```

### Q5: 如何调试问题？

1. **查看日志**
```bash
# Docker
docker-compose logs -f

# Systemd
sudo journalctl -u workorder-automation -f
```

2. **测试配置**
```bash
# 在本地测试 .env 配置是否正确
python -c "from src.utils.config import get_config; c = get_config(); print('配置加载成功')"
```

3. **手动运行测试**
```bash
# Docker
docker-compose run --rm workorder-automation python -c "print('测试')"

# Systemd
sudo -u workorder /opt/workorder-automation/venv/bin/python main.py
```

---

## 安全建议

1. **文件权限**
```bash
# .env 文件权限设置为 600
chmod 600 /opt/workorder-automation/.env

# 目录权限
chown -R workorder:workorder /opt/workorder-automation
```

2. **防火墙配置**
- 仅开放必要的端口
- 使用 VPN 或内网访问管理接口

3. **定期更新**
```bash
# 更新系统
sudo apt-get update && sudo apt-get upgrade

# 更新 Python 依赖
pip install --upgrade -r requirements.txt
```

---

## 联系支持

部署遇到问题？
1. 查看日志定位问题
2. 检查环境变量配置
3. 确认网络连接正常
