# Agent外贸获客 rendae

> 全自动外贸客户开发系统 —— 从自然语言指令到客户触达的自动化闭环

## 功能特性

- 🔍 **客户搜索**：支持 SerpAPI、Google CSE、Bing 三大搜索引擎，及 LinkedIn、B2B 平台定向搜索
- 🕸️ **官网爬取**：自动爬取目标网站，提取邮箱、电话、联系人、社交链接等关键信息
- 📊 **智能评分**：4 维度（网站质量 / 联系方式 / 行业匹配度 / 公司名称）评估客户质量，输出 A/B/C/D 等级
- 💌 **开发信生成**：12 种 AI 邮件模板（标准 / 个性化 / 跟进 / 冷邮件等），支持 SMTP 单发与批量发送
- 📋 **CRM 管理**：基于飞书多维表格 / JSON 文件的客户数据增删改查与搜索
- ⏰ **定时调度**：Cron 表达式驱动的自动获客任务
- 🔒 **安全防护**：API Key 认证、速率限制、SSRF 防护、XSS 清理

## 系统架构

```
┌─────────────────────────────────────────────────────┐
│                    Web 前端 (HTML)                   │
│   仪表盘 / 一键获客 / 搜索 / 爬取 / 评分 / 邮件 / CRM  │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│               FastAPI 后端服务                       │
│   API 认证 · 速率限制 · 安全防护 · 业务编排           │
└───┬───────┬────────┬─────────┬──────────┬───────────┘
    │       │        │         │          │
┌───▼─┐ ┌───▼────┐ ┌─▼──────┐ ┌▼───────┐ ┌▼────────┐
│搜索 │ │爬取    │ │评分    │ │CRM     │ │邮件     │
│插件 │ │插件    │ │插件    │ │插件    │ │插件     │
└─────┘ └────────┘ └───────┘ └───────┘ └─────────┘
```

## 快速开始

### 方式一：一键启动（推荐）

```bash
chmod +x start.sh
./start.sh setup    # 环境检查与依赖安装
./start.sh start    # 启动 Web 服务
```

启动后访问：http://localhost:8000

### 方式二：手动启动

```bash
pip install -r requirements.txt
python web_backend.py
```

### 方式三：命令行模式

```bash
# 执行获客任务
python main.py skill --instruction "找10个美国的家具进口商"

# 定时任务模式
python main.py scheduler
```

## 项目结构

```
.
├── web_backend.py          # FastAPI 后端服务
├── web_frontend.html       # 单文件前端界面
├── web_simple.py           # 轻量 Web 启动器
├── main.py                 # CLI 入口
├── start.sh                # 启动管理脚本
├── config.yaml             # 配置文件
├── requirements.txt        # 依赖清单
├── mcp-plugins/            # MCP 插件
│   ├── search-plugin/      # 客户搜索插件
│   ├── crawl-plugin/       # 官网爬取插件
│   ├── score-plugin/       # 客户评分插件
│   ├── crm-plugin/         # CRM 管理插件
│   └── email-plugin/       # 开发信邮件插件
├── skills/                 # Skill 编排模块
│   └── trade_customer_skill/
├── scheduler/              # 定时调度器
├── utils/                  # 工具模块
│   ├── config.py           # 配置管理
│   ├── feishu_client.py    # 飞书 API 客户端
│   └── logger.py           # 日志模块
└── data/                   # 数据目录
    ├── crm_customers.json  # CRM 客户数据
    └── email_history.json  # 邮件发送历史
```

## 配置说明

复制 `.env.example` 为 `.env` 并填入你的配置：

| 配置项 | 说明 |
|--------|------|
| `FEISHU_APP_ID` / `FEISHU_APP_SECRET` | 飞书应用凭证（用于 CRM 多维表格） |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USERNAME` / `SMTP_PASSWORD` | SMTP 邮件服务器配置 |
| `SERPAPI_KEY` / `GOOGLE_CSE_ID` / `GOOGLE_API_KEY` / `BING_API_KEY` | 搜索引擎 API Key |

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/login` | API Key 登录 |
| GET | `/api/dashboard` | 仪表盘统计 |
| POST | `/api/workflow/start` | 一键获客工作流 |
| POST | `/api/search` | 客户搜索 |
| POST | `/api/crawl` | 官网爬取 |
| POST | `/api/score` | 客户评分 |
| GET/POST/PUT/DELETE | `/api/crm/...` | CRM 增删改查 |
| POST | `/api/email/generate` | 生成开发信 |
| POST | `/api/email/send` | 发送邮件 |
| GET/POST | `/api/smtp` | SMTP 配置管理 |

## 安全机制

- **API Key 认证**：所有 API 请求需携带有效 API Key
- **速率限制**：60 次 / 分钟、1000 次 / 小时
- **SSRF 防护**：禁止访问内网 IP、元数据服务等内部地址
- **XSS 防护**：所有用户输入与输出均经过 HTML 转义清理
- **密码安全**：SMTP 密码采用 SHA256 加盐哈希存储

## 许可证

MIT License
