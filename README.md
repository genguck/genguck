# Agent外贸获客 rendae

全自动外贸客户开发系统，通过自然语言指令驱动，自动完成客户搜索、官网爬取、联系方式提取、客户评分、CRM管理、开发信生成与邮件发送的完整闭环。

## ✨ 功能特性

- **客户搜索**：支持 SerpAPI / Google / Bing 多渠道客户线索搜索
- **官网爬取与联系方式提取**：自动抓取目标客户官网，提取邮箱、电话、联系人等信息
- **4维度客户评分**：基于 A / B / C / D 级别对客户进行智能分级
- **飞书多维表格 CRM 管理**：通过飞书开放平台 API 实现客户数据的结构化管理
- **12种 AI 邮件模板**：内置多种开发信模板，支持个性化生成
- **SMTP 邮件发送**：自动化触达客户，完成开发信投递
- **定时任务调度**：支持 Cron 表达式的定时任务调度
- **Web 管理界面**：提供 9 个功能标签页的可视化管理界面
- **API Key 认证与安全防护**：内置 SSRF / XSS 防护与速率限制

## 🛠 技术栈

- Python 3.11+
- FastAPI
- FastMCP
- BeautifulSoup4
- Schedule
- 飞书开放平台 API

## 📁 项目结构

```
.
├── main.py                      # 主程序入口
├── web_backend.py               # FastAPI 后端服务
├── web_frontend.html            # Web 管理前端界面
├── web_simple.py                # 简单 Web 界面启动器
├── start.sh                     # 启动脚本
├── config.yaml                  # 项目配置文件
├── .env.example                 # 环境变量示例文件
├── requirements.txt             # Python 依赖清单
├── skills/                      # Skill 技能模块
│   ├── trade_customer_skill/    # 外贸获客核心 Skill
│   └── trade-customer-skill/    # 外贸获客 Skill（备用命名）
├── scheduler/                   # 定时任务调度器
├── mcp-plugins/                 # MCP 插件集合
│   ├── search-plugin/           # 客户搜索插件
│   ├── crawl-plugin/            # 官网爬取插件
│   ├── crm-plugin/              # CRM 管理插件
│   ├── score-plugin/            # 客户评分插件
│   └── email-plugin/            # 邮件发送插件
├── utils/                       # 工具模块
│   ├── config.py                # 配置加载
│   ├── feishu_client.py         # 飞书 API 客户端
│   └── logger.py                # 日志模块
└── data/                        # 运行时数据
    ├── crm_customers.json
    └── email_history.json
```

## 🚀 快速开始

1. 复制 `.env.example` 为 `.env` 并填写配置
2. 安装依赖：`pip install -r requirements.txt`
3. 运行：`bash start.sh` 或 `python main.py`

## ⚙️ 配置说明

- **`config.yaml`**：项目主配置文件，包含应用信息、服务地址、飞书凭证、邮件 SMTP、搜索 API Key、CRM 表格字段及日志等配置
- **`.env`**：环境变量配置文件（由 `.env.example` 复制而来），用于存放敏感凭证与运行环境变量

## 📄 License

MIT
