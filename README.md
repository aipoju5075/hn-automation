# 工单自动化处理系统 v2.0

海南地区用户机/用户板自动出库流程系统 - 优化重构版

## 项目概述

本项目是对原工单自动化处理系统的全面优化重构，实现了更清晰的分层架构、更完善的错误处理、更安全的配置管理。

### 主要改进

| 方面 | 原项目 | 优化后 |
|------|--------|--------|
| 架构设计 | 单一文件，代码混杂 | 分层架构，职责分离 |
| 配置管理 | 硬编码 | YAML + 环境变量 |
| 日志系统 | print输出 | 标准logging + 文件轮转 |
| 类型安全 | 无类型注解 | 完整类型注解 |
| 数据模型 | 字典传参 | Pydantic模型 |
| 错误处理 | 简单try-except | 详细日志 + 异常分类 |
| 代码复用 | 大量重复 | 抽象基类 + 工具模块 |
| 安全 | 明文存储凭证 | 环境变量 + Cookie加密 |

## 项目结构

```
newproject/
├── config/
│   └── settings.yaml          # 主配置文件
├── data/
│   ├── cookies/              # Cookie存储目录
│   │   └── .gitkeep
│   └── files/                # 数据文件目录
│       └── .gitkeep
├── logs/                     # 日志目录
├── src/
│   ├── auth/                 # 认证模块
│   │   ├── base.py          # 认证基类
│   │   ├── workorder.py     # 工单系统认证
│   │   ├── asd.py           # ASD家电系统认证
│   │   └── logistics.py     # 大物流系统认证
│   ├── core/                 # 核心业务模块
│   │   ├── downloader.py    # 工单下载器
│   │   ├── picking.py       # 拣货处理器
│   │   └── shipping.py      # 发货处理器
│   ├── models/               # 数据模型
│   │   ├── sn_record.py     # SN记录模型
│   │   └── workorder.py     # 工单模型
│   ├── utils/                # 工具模块
│   │   ├── config.py        # 配置管理
│   │   ├── logger.py        # 日志配置
│   │   ├── encryption.py    # 加密工具
│   │   └── captcha.py       # 验证码识别
│   └── __init__.py
├── tests/                    # 测试目录
├── .env.example             # 环境变量示例
├── .gitignore               # Git忽略配置
├── main.py                  # 主程序入口
├── requirements.txt         # 依赖列表
└── README.md                # 项目说明
```

## 架构设计

### 分层架构

```
┌─────────────────────────────────────────────────────────────┐
│                        主程序 (main.py)                       │
│                    WorkOrderAutomation                       │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐    ┌────────────────┐    ┌──────────────────┐
│   认证层      │    │    业务层       │    │     工具层        │
│   (auth)     │    │    (core)      │    │     (utils)      │
├──────────────┤    ├────────────────┤    ├──────────────────┤
│ BaseAuth     │    │ WorkOrder      │    │ Config           │
│ WorkOrderAuth│    │ Downloader     │    │ Logger           │
│ ASDAuth      │    │ Picking        │    │ AESCipher        │
│ LogisticsAuth│    │ Processor      │    │ Captcha          │
│              │    │ Shipping       │    │ Recognizer       │
│              │    │ Processor      │    │                  │
└──────────────┘    └────────────────┘    └──────────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              ▼
                    ┌──────────────────┐
                    │    数据模型层      │
                    │    (models)      │
                    ├──────────────────┤
                    │ SNRecord         │
                    │ PickingRecord    │
                    │ ShippingRecord   │
                    │ WorkOrder        │
                    └──────────────────┘
```

### 核心流程

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ 工单系统  │───▶│ 下载工单  │───▶│ 解析SN   │───▶│ ASD拣货  │
│  登录     │    │   CSV    │    │   列表   │    │          │
└──────────┘    └──────────┘    └──────────┘    └────┬─────┘
                                                     │
                              ┌──────────────────────┘
                              ▼
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ 发货完成  │◀───│ 执行发货  │◀───│获取待发货│◀───│大物流登录│
│          │    │          │    │  数据    │    │          │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
```

## 模块详解

### 1. 认证模块 (src/auth/)

#### BaseAuth - 认证基类
- 提供统一的Session管理
- Cookie的保存/加载/清除
- HTTP请求封装 (GET/POST)

#### WorkOrderAuth - 工单系统认证
- 验证码自动识别 (百度OCR)
- AES动态密钥加密
- Cookie持久化登录
- 自动重试机制

#### ASDAuth - ASD家电系统认证
- 简洁的登录流程
- 适用于RF拣货接口

#### LogisticsAuth - 大物流系统认证
- 标准Web登录
- 发货接口认证

### 2. 核心业务模块 (src/core/)

#### WorkOrderDownloader - 工单下载器
- 下载已完成工单CSV
- CSV解析和SN提取
- 自动识别产品类型

#### PickingProcessor - 拣货处理器
- 四步拣货流程：
  1. 查询SN信息
  2. 创建出货单
  3. 查询拣货详情
  4. 确认拣货
- 批量处理能力
- 完整错误追踪

#### ShippingProcessor - 发货处理器
- 分页获取待发货数据
- 自动区分自提/外发
- 支持批量发货
- 人员白名单管理

### 3. 数据模型 (src/models/)

使用 Pydantic 进行数据验证和序列化：

```python
class SNRecord(BaseModel):
    sn_code: str              # SN编码
    product_type: ProductType # 产品类型
    order_no: Optional[str]   # 订单号
    customer_name: Optional[str]  # 客户姓名
    status: Optional[str]     # 状态

class PickingRecord(BaseModel):
    sn_code: str
    so_no: str
    success: bool
    message: Optional[str]
    picked_at: Optional[datetime]

class ShippingRecord(BaseModel):
    sn_code: str
    so_no: str
    is_self_pickup: bool
    tracking_no: Optional[str]
    success: bool
    message: Optional[str]
```

### 4. 工具模块 (src/utils/)

#### Config - 配置管理
- YAML配置文件
- 环境变量覆盖
- 点号路径访问：`config.get("system.interval")`

#### Logger - 日志系统
- 控制台 + 文件双输出
- 日志轮转 (10MB/文件，保留5个)
- 统一格式：`时间 - 名称 - 级别 - 消息`

#### AESCipher - 加密工具
- AES-CBC with Zero Padding
- 兼容原系统加密逻辑
- 支持加密/解密

#### CaptchaRecognizer - 验证码识别
- 基于百度OCR API
- 支持中英文识别
- 自动去除空格
- 重试机制

## 配置说明

### 环境变量 (.env)

```bash
# 工单系统
WORKORDER_USERNAME=your_username
WORKORDER_PASSWORD=your_password

# ASD家电系统
ASD_USERNAME=your_username
ASD_PASSWORD=your_password

# 大物流系统
LOGISTICS_USERNAME=your_username
LOGISTICS_PASSWORD=your_password

# 自提人员名单
SELF_PICKUP_STAFF=陈起,陈双强,黄道章,李亮,王运孝,谢小习,陈海亮,唐殿岳
```

### 配置文件 (config/settings.yaml)

```yaml
system:
  interval: 30              # 循环间隔（分钟）
  max_retry: 5              # 验证码重试次数
  log_level: INFO           # 日志级别

urls:
  workorder:
    base: "https://gd.anyserves56.com"
    # ... 各端点配置
  asd:
    base: "https://www.anyserves56.com"
    # ...
  logistics:
    base: "https://www.anyserves56.com"
    # ...

paths:
  cookies: "./data/cookies/cookies.json"
  log: "./logs/app.log"
  # ...
```

## 部署到服务器

### 快速部署（Docker）

```bash
# 1. 上传到服务器，进入项目目录
cd workorder-automation

# 2. 配置环境变量
cp .env.example .env
nano .env  # 填入配置

# 3. 启动
docker-compose up -d
```

### 详细部署文档

查看 [DEPLOY.md](DEPLOY.md) 获取：
- Docker 部署方案
- Systemd 服务部署
- Supervisor 部署
- 服务器配置要求
- 常见问题排查

## 使用方法

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入实际凭证
```

### 3. 运行程序

```bash
# 单次执行
python main.py

# 或在Python中调用
from main import WorkOrderAutomation

automation = WorkOrderAutomation()
automation.run_once()  # 单次执行
# automation.run_loop()  # 循环执行
```

## 与原项目对比

### 代码质量提升

| 指标 | 原项目 | 优化后 |
|------|--------|--------|
| 文件数 | 3个 | 15+个 |
| 代码行数 | ~600行 | ~2000行（含注释和文档）|
| 重复代码 | 多处重复 | 通过继承和工具函数消除 |
| 类型注解 | 0% | 100% |
| 文档字符串 | 极少 | 完整覆盖 |
| 配置硬编码 | 多处 | 全部可配置 |

### 功能增强

1. **更完善的日志**
   - 原项目：`print("登录成功")`
   - 优化后：`logger.info("工单系统登录成功", extra={"user": username})`

2. **更安全的凭证管理**
   - 原项目：明文写在代码中
   - 优化后：环境变量 + .env文件

3. **更清晰的错误处理**
   - 原项目：`except Exception as e: print(e)`
   - 优化后：分类异常 + 详细日志 + 重试机制

4. **更好的可测试性**
   - 原项目：紧密耦合
   - 优化后：依赖注入 + 抽象接口

## 扩展建议

1. **添加测试**
   ```bash
   tests/
   ├── test_auth.py
   ├── test_downloader.py
   └── test_integration.py
   ```

2. **添加监控**
   - 成功率统计
   - 钉钉/企业微信通知
   - 数据可视化面板

3. **API封装**
   - 使用FastAPI提供REST接口
   - 支持远程触发和查询

4. **~~容器化~~** ✅ 已完成
   - 提供 Dockerfile 和 docker-compose.yml
   - 支持一键部署

5. **~~异常通知~~** ✅ 已完成
   - 集成 PushPlus 微信通知
   - 登录失败、系统异常自动告警

## 许可证

MIT License
