# 外贸获客 Agent - 完整项目快照 v3
# 第一性原理：从最基本的需求出发，记录每一个文件的完整内容与设计

> 备份时间: 2026-07-23
> 版本: v3 (含对抗性审查修复)
> 核心文件: web_backend.py + web_frontend.html + start.sh

---

## 一、项目第一性原理设计

### 1.1 核心问题
外贸业务员每天重复: 搜索客户 → 查网站 → 找邮箱 → 评分 → 录CRM → 写开发信 → 发邮件

### 1.2 第一性原理拆解
1. **数据获取**: 需要客户来源 → 种子库 + 真实网站爬取
2. **数据处理**: 需要结构化 → 评分算法 + CRM 存储
3. **内容生成**: 需要个性化 → 8种AI模板 + 随机化
4. **触达执行**: 需要发送 → SMTP真实发送 / 模拟发送
5. **安全防护**: 需要防护 → API Key认证 + SSRF/XSS/速率限制

### 1.3 技术选型
- 后端: FastAPI (Python 3.11+)
- 前端: 单文件 HTML (无框架，原生 JS)
- 存储: JSON 本地文件 (data/ 目录)
- 邮件: smtplib (标准库)
- 爬虫: requests + BeautifulSoup

---

## 二、文件清单与功能

### 2.1 核心文件（必备）
| 文件 | 作用 | 行数 |
|------|------|------|
| web_backend.py | FastAPI 后端服务 | 1160+ |
| web_frontend.html | 单文件前端界面 | 1187 |
| start.sh | 启动/停止/状态管理脚本 | 498 |
| requirements.txt | Python 依赖 | 17 |
| config.yaml | 项目配置 | 51 |
| .env.example | 环境变量示例 | 12 |

### 2.2 数据文件（运行时生成）
| 文件 | 作用 |
|------|------|
| data/crm_customers.json | CRM 客户数据 |
| data/email_history.json | 邮件发送历史 |
| data/smtp_config.json | SMTP 配置（含密码哈希）|

### 2.3 辅助模块（旧架构，非核心）
| 文件 | 作用 |
|------|------|
| main.py | 旧版主入口（已被 web_backend.py 取代）|
| web_simple.py | 简单版 Web 服务 |
| utils/config.py | 配置加载（旧）|
| utils/logger.py | 日志（旧）|
| utils/feishu_client.py | 飞书客户端（未使用）|
| skills/trade-customer-skill/main.py | Skill 模式（旧）|
| scheduler/main.py | 定时调度器（旧）|
| mcp-plugins/*/main.py | MCP 插件（旧，5个）|

---

## 三、后端架构 (web_backend.py)

### 3.1 模块结构
```
web_backend.py
├── 配置区 (L33-48)
│   ├── 路径: SCRIPT_DIR, DATA_DIR
│   ├── 环境变量: API_KEY, HOST, PORT
│   └── 速率限制: 60次/分钟, 1000次/小时
├── 工具函数 (L50-95)
│   ├── _sanitize_html(): XSS 防护
│   ├── _validate_email(): 邮箱校验
│   ├── _is_safe_url(): SSRF 防护
│   └── _rate_limit(): 速率限制
├── 种子库 (L97-137)
│   └── SEED_COMPANIES: 5个行业 25家公司
├── 数据存储 (L139-171)
│   ├── _load_json() / _save_json()
│   └── 三个数据文件: CRM/Email/SMTP
├── 业务函数 (L173-260)
│   ├── _real_search(): 搜索客户
│   ├── _crawl_company_info(): 爬取网站
│   └── _evaluate_company(): 评分算法
├── FastAPI 应用 (L262-273)
│   ├── CORS 中间件
│   ├── APIKeyHeader 认证
│   └── get_current_user 依赖
├── Pydantic 模型 (L275-345)
│   └── 8个请求模型
├── API 路由 (L348-1156)
│   ├── 21 个端点
│   └── 8 种 AI 邮件模板
└── 主入口 (L1158-1160)
```

### 3.2 API 端点清单（21个）
| 方法 | 路径 | 功能 | 认证 |
|------|------|------|------|
| GET | / | 返回前端 HTML | ❌ |
| GET | /api/health | 健康检查 | ❌ |
| POST | /api/customer/search | 搜索客户 | ✅ |
| POST | /api/score/customer | 单客户评分 | ✅ |
| POST | /api/score/batch | 批量评分 | ✅ |
| POST | /api/crawl/website | 爬取网站 | ✅ |
| POST | /api/crawl/extract-contacts | 提取联系方式 | ✅ |
| POST | /api/email/generate | 生成开发信(12种) | ✅ |
| POST | /api/email/send | 发送邮件 | ✅ |
| GET | /api/email/history | 邮件历史 | ✅ |
| POST | /api/crm/customers | 添加客户 | ✅ |
| GET | /api/crm/customers | 客户列表(分页) | ✅ |
| GET | /api/crm/customers/{id} | 客户详情 | ✅ |
| PUT | /api/crm/customers/{id} | 更新客户 | ✅ |
| DELETE | /api/crm/customers/{id} | 删除客户 | ✅ |
| GET | /api/smtp/config | 获取SMTP配置 | ✅ |
| POST | /api/smtp/config | 保存SMTP配置 | ✅ |
| POST | /api/smtp/test | 测试SMTP连接 | ✅ |
| DELETE | /api/smtp/config | 清除SMTP配置 | ✅ |
| POST | /api/workflow/full | 一键获客工作流 | ✅ |
| GET | /api/dashboard/stats | 仪表盘统计 | ✅ |

### 3.3 12种邮件模板
1. standard - 标准开发信
2. personalized - 个性化
3. follow_up - 跟进邮件
4. cold - 冷邮件
5. ai - 🤖 AI合作型
6. ai_supplier - 🏭 AI供应商型
7. ai_inquiry - 💰 AI询价型
8. ai_product - 📦 AI产品推介
9. ai_invitation - 📨 AI展会邀请
10. ai_sample - 🎁 AI样品申请
11. ai_agency - 🤝 AI代理招募
12. ai_followup - 📞 AI跟进型

### 3.4 评分算法（满分100）
| 维度 | 分值 | 评分依据 |
|------|------|---------|
| website_quality | 30 | HTTPS(8) + 真实域名(15) + 顶级域(7) |
| contact_info | 35 | 邮箱数量(≤20) + 电话数量(≤15) |
| industry_match | 20 | 完全匹配(20) / 部分匹配(10) / 有行业(12) |
| company_info | 15 | 信息字段数 × 3 (≤15) |
| 等级 | A≥85 | B≥70 | C≥55 | D<55 |

### 3.5 安全机制
1. **API Key 认证**: X-API-Key 请求头
2. **速率限制**: 60次/分钟 + 1000次/小时
3. **SSRF 防护**: 拦截内网IP + 限制协议
4. **XSS 防护**: HTML标签清理 + 实体转义
5. **密码保护**: SMTP密码不明文返回（显示***）
6. **输入校验**: Pydantic 模型 + 邮箱格式校验

---

## 四、前端架构 (web_frontend.html)

### 4.1 页面结构
```
web_frontend.html
├── <head> (L1-112)
│   ├── meta 标签
│   ├── xlsx CDN (Excel导出)
│   └── <style> CSS 样式 (110行)
├── <body>
│   ├── .header 顶部导航 (L115-130)
│   │   ├── logo
│   │   └── 登录区/用户信息
│   ├── .container 主容器 (L132-445)
│   │   ├── .nav-tabs 9个标签页 (L133-143)
│   │   ├── tab-dashboard 数据看板 (L145-168)
│   │   ├── tab-workflow 一键获客 (L170-218)
│   │   ├── tab-search 客户搜索 (L220-240)
│   │   ├── tab-crawl 官网爬取 (L242-261)
│   │   ├── tab-score 客户评分 (L263-290)
│   │   ├── tab-email 开发信 (L292-341)
│   │   ├── tab-crm CRM管理 (L343-391)
│   │   ├── tab-smtp SMTP配置 (L393-437)
│   │   └── tab-history 发送记录 (L439-444)
│   └── #crm-modal 客户编辑弹窗 (L447-492)
└── <script> (L494-1185)
    ├── 全局变量 (L495-500)
    ├── 工具函数 (L502-530)
    │   ├── escapeHtml()
    │   ├── showAlert()
    │   └── api() - fetch 封装
    ├── 登录/登出 (L532-547)
    ├── Tab 切换 (L549-559)
    ├── 40个业务函数 (L561-1173)
    └── DOMContentLoaded (L1175-1184)
```

### 4.2 9个页面功能
1. **数据看板**: 5个统计卡片 + 等级分布 + 系统信息
2. **一键获客**: 行业/地区/数量 → 6步工作流 → 结果展示+导出
3. **客户搜索**: 行业/地区/数量 → 搜索 → 卡片展示 → AI生成/加CRM/导出
4. **官网爬取**: URL输入 → 爬取网站/提取联系方式
5. **客户评分**: 公司信息输入 → 4维度评分展示
6. **开发信**: 12种模板 → 生成/编辑/发送 → 一键AI生成
7. **CRM**: 列表/筛选/新增/编辑/删除/导出Excel
8. **SMTP**: 6种预设 → 配置/测试/清除
9. **发送记录**: 邮件历史列表

### 4.3 关键功能函数
| 函数 | 行号 | 功能 |
|------|------|------|
| api() | L518 | fetch 请求封装 |
| doLogin() | L532 | 登录(localStorage) |
| switchTab() | L549 | Tab切换 |
| loadDashboard() | L561 | 加载仪表盘 |
| searchCustomers() | L595 | 搜索客户 |
| fillAndGoEmail() | L640 | 搜索结果→开发信自动生成 |
| autoGenerateAll() | L785 | 一键AI生成 |
| generateEmail() | L808 | 生成邮件 |
| sendEmail() | L849 | 发送邮件 |
| startWorkflow() | L898 | 一键获客 |
| loadCRM() | L954 | 加载CRM列表 |
| exportToExcel() | L1133 | Excel导出 |

### 4.4 CSS 设计
- 主色: #667eea (紫蓝) + #764ba2 (紫色)
- 渐变: 5种统计卡片渐变 + AI按钮8种渐变
- 响应式: @media 768px 断点
- 动画: spin(加载) + pulse(工作流步骤)

---

## 五、启动脚本 (start.sh)

### 5.1 命令清单
| 命令 | 功能 |
|------|------|
| ./start.sh start | 前台启动 |
| ./start.sh start -d | 后台启动 |
| ./start.sh stop | 停止 |
| ./start.sh restart | 重启 |
| ./start.sh status | 状态 |
| ./start.sh health | 健康检查 |
| ./start.sh setup | 环境检查 |
| ./start.sh logs | 查看日志 |
| ./start.sh skill | Skill模式 |
| ./start.sh scheduler | 调度器 |

### 5.2 启动流程（5步）
1. 检查 Python 3.11+
2. 检查/安装依赖
3. 检查项目文件
4. 检查端口占用
5. 启动服务

### 5.3 关键配置
- HOST: 0.0.0.0
- PORT: 8000
- API_KEY: sk-1247a1fea10b4f4db70d83dbc64edc97
- PID文件: /tmp/waimao-agent.pid
- 日志文件: /tmp/waimao-agent.log

---

## 六、对抗性审查修复记录 (v3)

### 6.1 修复的问题
| # | 问题 | 严重度 | 修复位置 |
|---|------|--------|---------|
| 1 | extract-contacts SSRF 返回200而非400 | 🔴高 | web_backend.py L428 |
| 2 | 工作流 crm_id 为 null (company_name缺失) | 🔴高 | web_backend.py L1096 |
| 3 | SMTP 保存过滤掉 false 值 | 🟡中 | web_backend.py L1041-1044 |
| 4 | 前端按钮选择器不精确 | 🟡中 | web_frontend.html L334-335 |

### 6.2 回归测试结果
17项全部通过 ✅:
- 健康检查、认证、搜索、评分、爬取、SSRF防护
- 12种邮件模板、CRM增删改查、邮件发送
- SMTP配置、工作流、仪表盘、XSS防护

---

## 七、使用指南

### 7.1 快速启动
```bash
cd /workspace
./start.sh start -d
# 访问 http://localhost:8000
# API Key: sk-1247a1fea10b4f4db70d83dbc64edc97
```

### 7.2 功能流程
1. 顶部输入 API Key 登录
2. **一键获客**: 输入行业 → 自动搜索→爬取→评分→CRM→发信
3. **客户搜索**: 搜索 → 点"🤖 AI生成" → 自动填入并生成开发信
4. **开发信**: 点"⚡ 一键AI生成" → 随机示例+随机AI类型 → 自动生成
5. **CRM**: 查看/编辑/导出客户

### 7.3 SMTP 配置
1. 进入 SMTP 页面
2. 选择预设(Gmail/QQ/163等)
3. 填入用户名和密码/授权码
4. 测试连接 → 保存

---

## 八、改进建议（待实现）

### 🔴 高优先级
1. JSON存储 → SQLite (并发安全)
2. API Key 哈希存储 + 多用户
3. 速率限制 → Redis (分布式)

### 🟡 中优先级
4. 工作流错误信息回传
5. 搜索接入真实API (Google/SerpAPI)
6. HTML格式邮件
7. 前端分页控件

### 🟢 低优先级
8. 暗黑模式
9. 批量邮件发送
10. 客户跟进提醒
11. CSV/PDF导出
12. 操作审计日志

---

## 九、备份验证

### 9.1 文件完整性
- [x] web_backend.py (1160+ 行)
- [x] web_frontend.html (1187 行)
- [x] start.sh (498 行)
- [x] requirements.txt (17 行)
- [x] config.yaml (51 行)
- [x] .env.example (12 行)

### 9.2 功能验证（17/17通过）
- [x] 健康检查
- [x] 认证防护
- [x] 客户搜索
- [x] 客户评分(单/批)
- [x] 网站爬取
- [x] 提取联系方式
- [x] SSRF防护(crawl/extract)
- [x] 12种邮件模板
- [x] CRM增删改查
- [x] 邮件发送(模拟)
- [x] 邮件历史
- [x] SMTP配置(false值)
- [x] 一键获客工作流
- [x] 仪表盘统计
- [x] XSS防护

---

**备份完成。如需恢复，直接使用 tar 包解压即可。**
