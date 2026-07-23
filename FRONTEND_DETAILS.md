# Agent外贸获客 rendae - 前端页面详细结构文档

> 版本: v1.0
> 文件: web_frontend.html (1187 行)
> 技术: 原生 HTML + CSS + JavaScript (无框架)
> 依赖: xlsx.js (CDN, Excel导出)

---

## 一、整体页面结构

### 1.1 页面层级结构

```
HTML 文档 (1187行)
├── <head> 头部 (L1-L111)
│   ├── meta 标签 (charset, viewport)
│   ├── title 页面标题
│   ├── xlsx.js CDN 引入
│   └── <style> 样式 (L8-L110, 共 103 行 CSS)
│
├── <body> 主体 (L113-L1186)
│   ├── .header 顶部导航栏 (L115-L130, 16行)
│   │   ├── .logo 左侧 Logo 区
│   │   │   ├── .logo-icon (🎯 图标)
│   │   │   └── .logo-text (Agent外贸获客 rendae)
│   │   └── .header-right 右侧用户区
│   │       ├── #login-area 登录输入区 (默认显示)
│   │       │   ├── #api-key-input 输入框 (password类型)
│   │       │   └── 登录按钮
│   │       └── #user-info 已登录信息区 (默认隐藏)
│   │           ├── #user-label (✓ 已登录)
│   │           └── 退出按钮
│   │
│   ├── .container 主容器 (L132-L445)
│   │   ├── .nav-tabs 标签导航栏 (L133-L143)
│   │   │   └── 9 个 Tab 按钮
│   │   │
│   │   ├── #tab-dashboard 数据看板 (L145-L168)
│   │   ├── #tab-workflow 一键获客 (L170-L218)
│   │   ├── #tab-search 客户搜索 (L220-L240)
│   │   ├── #tab-crawl 官网爬取 (L242-L261)
│   │   ├── #tab-score 客户评分 (L263-L290)
│   │   ├── #tab-email 开发信 (L292-L341)
│   │   ├── #tab-crm CRM 管理 (L343-L391)
│   │   ├── #tab-smtp SMTP 配置 (L393-L437)
│   │   └── #tab-history 发送记录 (L439-L444)
│   │
│   └── #crm-modal 客户编辑弹窗 (L447-L492)
│       └── 弹窗内容区 (600px宽, 90vh高, 居中)
│
└── <script> JavaScript (L494-L1185, 共 692 行 JS)
    ├── 全局变量 (6个)
    ├── 工具函数 (3个: escapeHtml, showAlert, api)
    ├── 登录/登出 (2个函数)
    ├── Tab 切换 (1个函数)
    ├── 业务函数 (~30+个)
    └── DOMContentLoaded 初始化
```

---

## 二、CSS 样式详细说明 (103 行)

### 2.1 基础样式 (L9-L10)

| 选择器 | 样式属性 | 值 |
|--------|---------|-----|
| * | margin, padding | 0 |
| * | box-sizing | border-box |
| body | font-family | -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', sans-serif |
| body | background | #f0f2f5 |
| body | color | #1f2937 |

### 2.2 顶部导航栏 (L11-L27)

**`.header`** - 顶部栏
- 背景: linear-gradient(135deg, #667eea 0%, #764ba2 100%)
- 文字: 白色
- padding: 14px 28px
- 布局: flex, 两端对齐, 垂直居中
- 阴影: 0 4px 12px rgba(102,126,234,0.3)
- 定位: sticky, top:0, z-index:100

**`.logo`** - Logo 区
- display: flex, align-items: center, gap: 10px
- .logo-icon: font-size 24px
- .logo-text: font-size 18px, font-weight 600

**`.header-right`** - 右侧区
- display: flex, align-items: center, gap: 12px

**`#api-key-input`** - API Key 输入框
- padding: 7px 12px
- border: 1px solid rgba(255,255,255,0.3)
- border-radius: 8px
- font-size: 13px
- width: 200px
- background: rgba(255,255,255,0.15)
- color: white
- placeholder: rgba(255,255,255,0.6)

### 2.3 按钮样式 (L18-L27)

**`.btn`** 基础按钮
- padding: 7px 16px
- border: none, border-radius: 8px
- font-size: 13px, font-weight: 500
- cursor: pointer
- display: inline-flex, align-items: center, gap: 5px
- transition: all 0.2s

**`:hover`** 悬停效果
- transform: translateY(-1px)
- box-shadow: 0 4px 8px rgba(0,0,0,0.1)

**按钮颜色变体:**

| 类名 | 背景色 | 文字色 |
|------|--------|--------|
| .btn-primary | #fff | #667eea |
| .btn-success | #10b981 | white |
| .btn-warning | #f59e0b | white |
| .btn-danger | #ef4444 | white |
| .btn-info | #3b82f6 | white |
| .btn-ghost | rgba(255,255,255,0.15) | white |

**`.btn-sm`** - 小按钮: padding 4px 10px, font-size 12px
**`:disabled`** - 禁用: opacity 0.5, cursor not-allowed

### 2.4 容器与 Tab (L28-L34)

**`.container`** - 主容器
- max-width: 1400px
- margin: 0 auto
- padding: 20px

**`.nav-tabs`** - Tab 导航
- display: flex, gap: 4px
- background: white
- border-radius: 12px 12px 0 0
- padding: 0 16px
- border-bottom: 2px solid #e5e7eb
- overflow-x: auto
- box-shadow: 0 1px 3px rgba(0,0,0,0.05)

**`.tab`** - Tab 项
- padding: 16px 20px
- cursor: pointer
- font-size: 14px, font-weight: 500
- color: #6b7280
- border-bottom: 2px solid transparent
- margin-bottom: -2px
- transition: all 0.2s
- white-space: nowrap

**`.tab.active`** - 激活状态
- color: #667eea
- border-bottom-color: #667eea
- font-weight: 600

**`.tab-content`** - Tab 内容区
- display: none
- background: white
- border-radius: 0 0 12px 12px
- padding: 24px
- box-shadow: 0 4px 12px rgba(0,0,0,0.05)

**`.tab-content.active`** - 激活显示: display block

### 2.5 卡片组件 (L35-L36)

**`.card`** - 卡片容器
- background: white
- border: 1px solid #e5e7eb
- border-radius: 12px
- padding: 20px
- margin-bottom: 16px

**`.card-title`** - 卡片标题
- font-size: 16px, font-weight: 600
- margin-bottom: 16px
- display: flex, align-items: center, gap: 10px

### 2.6 统计卡片 (L37-L45)

**`.stats-grid`** - 统计网格
- display: grid
- grid-template-columns: repeat(auto-fit, minmax(180px, 1fr))
- gap: 14px
- margin-bottom: 20px

**`.stat-card`** - 统计卡片
- 背景渐变: linear-gradient(135deg, #667eea 0%, #764ba2 100%)
- 文字: 白色
- padding: 20px
- border-radius: 12px
- text-align: center

**6 种渐变色 (nth-child):**

| 序号 | 渐变起始色 | 渐变结束色 |
|------|-----------|-----------|
| 1 (默认) | #667eea | #764ba2 |
| 2 | #f093fb | #f5576c |
| 3 | #4facfe | #00f2fe |
| 4 | #43e97b | #38f9d7 |
| 5 | #fa709a | #fee140 |
| 6 | #30cfd0 | #330867 |

**`.stat-num`** - 数字: font-size 32px, font-weight 700, margin-bottom 4px
**`.stat-label`** - 标签: font-size 13px, opacity 0.9

### 2.7 表单样式 (L46-L50)

**`.form-row`** - 行布局
- display: flex, gap: 14px
- margin-bottom: 14px
- flex-wrap: wrap

**`.form-group`** - 表单项
- flex: 1, min-width: 150px

**`.form-group label`** - 标签
- display: block
- font-size: 13px, font-weight: 500
- color: #374151
- margin-bottom: 6px

**`.form-group input/select/textarea`** - 输入控件
- width: 100%
- padding: 9px 12px
- border: 1px solid #d1d5db
- border-radius: 8px
- font-size: 13px
- background: #fafafa

**:focus** - 聚焦状态
- outline: none
- border-color: #667eea
- background: white

### 2.8 客户卡片 (L51-L62)

**`.customer-grid`** - 客户网格
- display: grid
- grid-template-columns: repeat(auto-fill, minmax(280px, 1fr))
- gap: 12px

**`.customer-card`** - 客户卡片
- border: 1px solid #e5e7eb
- border-radius: 10px
- padding: 16px
- transition: all 0.2s
- background: #fafafa

**:hover** - 悬停
- border-color: #667eea
- background: white
- transform: translateY(-2px)
- box-shadow: 0 8px 16px rgba(102,126,234,0.1)

**`.customer-name`** - 公司名: font-size 15px, font-weight 600, color #1f2937
**`.customer-web`** - 网站: font-size 12px, color #667eea, word-break break-all
**`.customer-info`** - 信息: font-size 12px, color #6b7280, line-height 1.8
**`.customer-footer`** - 底部: flex, space-between, align-items center, padding-top 10px, border-top 1px solid #e5e7eb

**`.level-badge`** - 等级徽章
- padding: 3px 10px
- border-radius: 12px
- font-size: 11px, font-weight: 600

**等级颜色:**
- .level-A: background #d1fae5, color #065f46
- .level-B: background #dbeafe, color #1e40af
- .level-C: background #fef3c7, color #92400e
- .level-D: background #f3f4f6, color #4b5563

### 2.9 评分详情 (L63-L68)

**`.score-detail`** - 评分容器: flex column, gap 6px, margin 8px 0
**`.score-row`** - 行: flex, align-items center, gap 8px, font-size 12px
**`.score-label`** - 标签: width 80px, color #6b7280, flex-shrink 0
**`.score-bar`** - 进度条容器: flex 1, height 6px, background #e5e7eb, border-radius 3px, overflow hidden
**`.score-bar-fill`** - 进度条填充: height 100%, 渐变 linear-gradient(90deg, #667eea, #764ba2), border-radius 3px
**`.score-num`** - 分数: width 30px, text-align right, color #374151, font-weight 500

### 2.10 邮件模板选择 (L69-L72)

**`.template-bar`** - 模板按钮栏: display flex, gap 8px, margin-bottom 16px, flex-wrap wrap
**`.template-btn`** - 模板按钮
- padding: 6px 14px
- border: 1px solid #d1d5db
- border-radius: 20px
- background: white
- font-size: 12px
- cursor: pointer
- color: #6b7280

**.template-btn.active** - 激活: background #667eea, color white, border-color #667eea

**`.email-preview`** - 邮件预览
- background: #f9fafb
- border: 1px solid #e5e7eb
- border-radius: 10px
- padding: 18px
- white-space: pre-wrap
- font-size: 13px
- line-height: 1.8
- max-height: 400px, overflow-y: auto

### 2.11 CRM 表格 (L73-L76)

**`.crm-table`** - 表格: width 100%, border-collapse collapse, font-size 13px
**th** - 表头: text-align left, padding 12px, background #f9fafb, font-weight 600, color #374151, border-bottom 2px solid #e5e7eb
**td** - 单元格: padding 12px, border-bottom 1px solid #f3f4f6, color #4b5563
**tr:hover** - 悬停行: background #f9fafb

### 2.12 SMTP 配置 (L77-L80)

**`.smtp-grid`** - SMTP 网格: display grid, grid-template-columns 1fr 1fr, gap 14px

**`.status-dot`** - 状态点: display inline-block, width/height 8px, border-radius 50%, margin-right 6px
- .status-success: #10b981
- .status-error: #ef4444

### 2.13 历史记录 (L81-L86)

**`.history-item`** - 历史项: border 1px solid #e5e7eb, border-radius 10px, padding 14px, margin-bottom 10px
**`.history-row`** - 行: flex, space-between, align-items center, margin-bottom 6px
**`.history-company`** - 公司名: font-weight 600, font-size 14px, color #1f2937
**`.history-status`** - 状态: padding 2px 10px, border-radius 12px, font-size 11px, font-weight 500
- .history-sent: background #d1fae5, color #065f46
- .history-sim: background #fef3c7, color #92400e

### 2.14 动画与辅助 (L87-L110)

**`.loading`** - 加载动画
- display inline-block, width/height 16px
- border 2px solid #e5e7eb, border-top-color #667eea
- border-radius 50%
- animation: spin 0.8s linear infinite
- margin-right 6px

**@keyframes spin** - 旋转: to { transform: rotate(360deg) }

**`.alert`** - 提示框
- padding: 12px 16px
- border-radius: 8px
- margin-bottom: 14px
- font-size: 13px
- display: none
- border-left: 4px solid

**.alert.show** - 显示: display block

**alert 颜色变体:**
- .alert-success: background #ecfdf5, color #065f46, border-left-color #10b981
- .alert-error: background #fef2f2, color #991b1b, border-left-color #ef4444
- .alert-info: background #eff6ff, color #1e40af, border-left-color #3b82f6
- .alert-warning: background #fffbeb, color #92400e, border-left-color #f59e0b

**`.two-col`** - 两栏布局: display grid, grid-template-columns 1fr 1fr, gap 16px

**`.workflow-steps`** - 工作流步骤: display flex, gap 8px, margin 16px 0, flex-wrap wrap, align-items center
**`.workflow-step`** - 步骤项: padding 8px 14px, border-radius 20px, font-size 12px, font-weight 500, background #f3f4f6, color #6b7280
- .done: background #d1fae5, color #065f46
- .active: background #dbeafe, color #1e40af, animation pulse 1.5s infinite

**@keyframes pulse** - 脉冲: 0%,100%{opacity:1} 50%{opacity:0.7}

**`.workflow-arrow`** - 箭头: color #9ca3af

**`.progress-bar`** - 进度条: height 8px, background #e5e7eb, border-radius 4px, overflow hidden, margin 12px 0
**`.progress-fill`** - 进度填充: height 100%, 渐变 linear-gradient(90deg, #667eea, #764ba2), border-radius 4px, transition width 0.3s ease

**`.empty-state`** - 空状态: text-align center, padding 40px 20px, color #9ca3af, font-size 14px

**`.badge`** - 徽章: display inline-block, padding 2px 8px, border-radius 6px, font-size 11px, font-weight 500, background #eef2ff, color #4f46e5

**`.action-btns`** - 操作按钮组: display flex, gap 6px, flex-wrap wrap

**`.config-status`** - 配置状态: display inline-flex, align-items center, gap 6px, padding 6px 12px, border-radius 8px, font-size 13px, font-weight 500
- .configured: background #d1fae5, color #065f46
- .not-configured: background #fee2e2, color #991b1b

**响应式 (@media max-width 768px):**
- .smtp-grid: 单列
- .two-col: 单列
- .form-row: 纵向排列

---

## 三、9 个标签页详细结构

### 3.1 Tab 1: 数据看板 (dashboard) - L145-L168

**元素清单:**
1. **`.stats-grid`** 统计卡片网格 (5个卡片)
   - #stat-customers: 总客户数
   - #stat-emails: 发送邮件
   - #stat-a: A级客户
   - #stat-rate: 转化率
   - #stat-score: 平均评分

2. **`.two-col`** 两栏布局
   - 左侧卡片: 🏆 客户等级分布 → #level-dist
   - 右侧卡片: 📈 系统信息
     - ✅ API 服务: 正常运行
     - ✅ 真实数据: 已接入
     - ✅ 安全防护: SSRF/XSS/速率限制
     - ✅ 数据存储: JSON本地存储

**关联函数:** `loadDashboard()` (L561-L593)

### 3.2 Tab 2: 一键获客 (workflow) - L170-L218

**卡片1: 🚀 一键获客全流程**
- 说明文字: 自动完成「客户搜索 → 官网爬取 → 联系方式提取 → 客户评分 → CRM录入 → 开发信发送」
- 第一行表单 (.form-row)
  - #wf-industry: 行业/产品 * (flex:2)
  - #wf-region: 目标地区
  - #wf-count: 数量 (number, 默认5, min1, max20)
- 第二行表单
  - #wf-product: 产品名称
  - #wf-template: 邮件模板 (下拉选择, 12个选项)
  - #wf-send-email: 自动发送开发信 (复选框)
- #wf-btn: 🚀 开始一键获客按钮 (btn-success, 15px字, padding 10px 24px)
- #wf-alert: 提示信息

**卡片2: 📊 执行结果 (#wf-result-card, 默认隐藏)**
- #wf-steps: 工作流步骤展示
- #wf-progress: 进度条
- #wf-summary: 结果总结文字
- #wf-export-btn: 📊 导出Excel (默认隐藏)
- #wf-results: 结果列表 (客户卡片网格)

**关联函数:** `startWorkflow()` (L898-L952), `exportWorkflowToExcel()` (L1170-L1173)

### 3.3 Tab 3: 客户搜索 (search) - L220-L240

**卡片1: 🔍 客户搜索**
- 表单行
  - #sc-industry: 行业/产品 (flex:2)
  - #sc-region: 目标地区
  - #sc-count: 数量 (number, 默认10, min1, max50)
- 按钮组
  - #sc-btn: 开始搜索 (btn-primary)
  - #sc-batch-score-btn: 批量评分 (btn-info, 默认禁用)
  - #sc-batch-crm-btn: 全部加入CRM (btn-success, 默认禁用)
  - #sc-export-btn: 📊 导出Excel (btn-success, 默认禁用)
- #sc-alert: 提示

**卡片2: 📋 搜索结果**
- #sc-count-label: 数量徽章 (0 个)
- #sc-results: 结果容器 (初始为 empty-state: "输入条件后点击搜索")

**关联函数:**
- `searchCustomers()` (L595-L611)
- `renderSearchResults()` (L613-L638)
- `fillAndGoEmail()` (L640-L652)
- `addOneToCRM()` (L654-L666)
- `batchScoreSearch()` (L668-L678)
- `batchAddCRM()` (L680-L695)
- `exportSearchToExcel()` (L1165-L1168)

### 3.4 Tab 4: 官网爬取 (crawl) - L242-L261

**卡片1: 🕸️ 官网爬取**
- #cr-url: 网站 URL * (flex:2)
- 按钮
  - 爬取网站 (btn-primary)
  - 提取联系方式 (btn-info)
- #cr-alert: 错误提示

**卡片2: 📄 爬取结果 (#cr-result-card, 默认隐藏)**
- #cr-title: 页面标题
- #cr-url-show: URL显示
- #cr-contacts: 联系方式区域
- #cr-content: 爬取内容 (email-preview样式, max-height 300px)

**关联函数:**
- `crawlWebsite()` (L697-L708)
- `extractContacts()` (L710-L731)

### 3.5 Tab 5: 客户评分 (score) - L263-L290

**卡片1: 📊 客户评分**
- 第一行
  - #sr-company: 公司名称 (flex:2)
  - #sr-industry: 行业
- 第二行
  - #sr-website: 网站
  - #sr-emails: 邮箱（逗号分隔）
  - #sr-phones: 电话（逗号分隔）
- 开始评分按钮 (btn-primary)

**卡片2: 📈 评分结果 (#sr-result-card, 默认隐藏)**
- 左侧: 总分 (#sr-total, 48px, 700粗细, 紫色) + "总分" 标签
- 右侧: 等级 (#sr-level)
- #sr-detail: 评分详情 (4个维度的进度条)

**关联函数:** `scoreCustomer()` (L733-L757)

### 3.6 Tab 6: 开发信 (email) - L292-L341

**卡片: ✉️ 开发信生成 & 发送**
- 第一行
  - #em-company: 公司名称 * (flex:2)
  - #em-to: 收件人邮箱 *
- 第二行
  - #em-contact: 联系人
  - #em-industry: 行业
  - #em-product: 产品名称
- 邮件类型选择 (3行template-bar)
  - 第一行: 标准开发信、个性化、跟进邮件、冷邮件
  - 第二行: 🤖 AI合作型、🏭 AI供应商型、💰 AI询价型、📦 AI产品推介
  - 第三行: 📨 AI展会邀请、🎁 AI样品申请、🤝 AI代理招募、📞 AI跟进型
- #em-subject: 邮件主题 (留空自动生成)
- #em-body: 邮件正文 (textarea, 10行, 留空自动生成)
- 按钮行
  - #em-gen-btn: 生成邮件 (btn-warning)
  - #em-send-btn: 📨 发送邮件 (btn-success)
  - ⚡ 一键AI生成按钮 (紫蓝渐变背景)
  - #em-smtp-status: SMTP状态提示
- #em-alert: 提示

**关联函数:**
- `selectEmailType()` (L759-L774)
- `autoGenerateAll()` (L785-L806)
- `generateEmail()` (L808-L847)
- `sendEmail()` (L849-L875)

### 3.7 Tab 7: CRM 管理 (crm) - L343-L391

**卡片: 📋 CRM 客户管理**
- 筛选行
  - #crm-filter-level: 等级筛选 (全部/A/B/C/D)
  - #crm-filter-status: 状态筛选 (全部/待开发/联系中/已成交/已失效)
  - + 新增客户按钮 (btn-primary)
  - 📊 导出Excel按钮 (btn-success)
- 表格区 (overflow-x:auto)
  - 表头: 公司名称、邮箱、评分/等级、状态、行业、操作
  - #crm-tbody: 表体 (初始: 暂无数据)
- #crm-pagination: 分页信息 (底部居中, 共 N 条)

**关联函数:**
- `loadCRM()` (L954-L979)
- `openCRMModal()` (L981-L991)
- `closeCRMModal()` (L993)
- `saveCRMFromModal()` (L995-L1013)
- `editCRM()` (L1015-L1031)
- `deleteCRM()` (L1033-L1037)
- `exportCRMToExcel()` (L1155-L1163)

### 3.8 Tab 8: SMTP 配置 (smtp) - L393-L437

**卡片: ⚙️ SMTP 配置**
- 标题栏: 标题 + #smtp-status-badge 状态徽章 (右对齐, margin-left:auto)
- #smtp-provider: 邮箱服务商预设 (下拉: 自定义/Gmail/QQ/163/Outlook/iCloud/Yahoo)
- .smtp-grid 双列网格 (6个字段)
  - #smtp-host: SMTP 主机
  - #smtp-port: 端口 (默认465)
  - #smtp-username: 用户名（邮箱）
  - #smtp-password: 密码 / 授权码 (password类型)
  - #smtp-from-email: 发件人邮箱
  - #smtp-from-name: 发件人名称
- 复选框行
  - #smtp-ssl: 使用 SSL (默认勾选)
  - #smtp-starttls: 使用 STARTTLS
- 按钮组
  - 保存配置 (btn-primary)
  - 测试连接 (btn-success)
  - 清除配置 (btn-danger)
- #smtp-alert: 提示

**关联函数:**
- `applySmtpPreset()` (L1048-L1057)
- `loadSmtpConfig()` (L1059-L1075)
- `saveSmtpConfig()` (L1077-L1093)
- `testSmtpConfig()` (L1095-L1100)
- `clearSmtpConfig()` (L1102-L1106)
- `updateSmtpStatusBadge()` (L884-L896)

**SMTP 预设数据 (PRESETS):**

| 服务商 | host | port | ssl | starttls |
|--------|------|------|-----|----------|
| gmail | smtp.gmail.com | 465 | true | false |
| qq | smtp.qq.com | 465 | true | false |
| 163 | smtp.163.com | 465 | true | false |
| outlook | smtp.office365.com | 587 | false | true |
| icloud | smtp.mail.me.com | 587 | false | true |
| yahoo | smtp.mail.yahoo.com | 465 | true | false |

### 3.9 Tab 9: 发送记录 (history) - L439-L444

**卡片: 📮 邮件发送记录**
- #history-list: 历史列表 (初始: 暂无发送记录)

**单条记录结构 (.history-item):**
- .history-row
  - .history-company: 公司名
  - .history-status: 状态 (已发送/模拟发送)
- 📧 收件人邮箱
- 📝 邮件主题
- 🕐 发送时间

**关联函数:** `loadHistory()` (L1108-L1131)

---

## 四、CRM 编辑弹窗 (#crm-modal) - L447-L492

**弹窗结构:**
- 遮罩: position fixed, 全屏, background rgba(0,0,0,0.5), z-index 1000
- 内容容器: background white, border-radius 12px, padding 24px, max-width 600px, width 90%, max-height 90vh, overflow-y auto

**表单字段:**
1. #crm-m-company: 公司名称 * (flex:2)
2. #crm-m-score: 评分 (number, 默认0, min0, max100)
3. #crm-m-email: 邮箱
4. #crm-m-phone: 电话
5. #crm-m-website: 网站
6. #crm-m-industry: 行业
7. #crm-m-level: 等级 (自动/A/B/C/D)
8. #crm-m-status: 状态 (待开发/联系中/已成交/已失效)
9. #crm-m-notes: 备注 (textarea, 3行)

**底部按钮:**
- 取消 (灰色背景)
- 保存 (btn-primary)

---

## 五、JavaScript 完整函数清单 (692行)

### 5.1 全局变量 (L495-L500)

| 变量名 | 初始值 | 说明 |
|--------|--------|------|
| API_BASE | '/api' | API 基础路径 |
| _authenticated | false | 是否已登录 |
| _emailType | 'standard' | 当前选中的邮件类型 |
| _searchResults | [] | 搜索结果缓存 |
| _crmEditId | null | CRM编辑的客户ID |
| _workflowResults | [] | 工作流结果缓存 |

### 5.2 工具函数 (3个)

| 函数名 | 行号 | 参数 | 返回值 | 功能 |
|--------|------|------|--------|------|
| escapeHtml() | L502 | s (string) | string | XSS防护: HTML转义 |
| showAlert() | L509 | id, msg, type | - | 显示提示框, 4秒后自动消失 |
| api() | L518 | path, method, body | Promise | fetch封装, 自动加API Key头, JSON解析 |

### 5.3 登录/登出 (2个)

| 函数名 | 行号 | 功能 |
|--------|------|------|
| doLogin() | L532 | 保存API Key到localStorage, 切换UI状态, 加载数据 |
| doLogout() | L542 | 移除localStorage中的API Key, 切换UI状态 |

### 5.4 Tab 切换 (1个)

| 函数名 | 行号 | 功能 |
|--------|------|------|
| switchTab(tab) | L549 | 切换Tab, 根据Tab加载对应数据 |

### 5.5 业务函数清单

| 函数名 | 行号 | 所属模块 | 功能 |
|--------|------|---------|------|
| loadDashboard() | L561 | 仪表盘 | 加载统计数据和等级分布 |
| searchCustomers() | L595 | 搜索 | 搜索客户 |
| renderSearchResults() | L613 | 搜索 | 渲染搜索结果卡片 |
| fillAndGoEmail() | L640 | 搜索 | 搜索结果→开发信自动跳转生成 |
| addOneToCRM() | L654 | 搜索 | 单个客户加入CRM |
| batchScoreSearch() | L668 | 搜索 | 批量评分搜索结果 |
| batchAddCRM() | L680 | 搜索 | 批量加入CRM |
| crawlWebsite() | L697 | 爬取 | 爬取网站内容 |
| extractContacts() | L710 | 爬取 | 提取联系方式 |
| scoreCustomer() | L733 | 评分 | 客户评分 |
| selectEmailType() | L759 | 邮件 | 选择邮件模板类型 |
| autoGenerateAll() | L785 | 邮件 | 一键AI生成 (随机示例+随机类型) |
| generateEmail() | L808 | 邮件 | 生成开发信 |
| sendEmail() | L849 | 邮件 | 发送邮件 |
| loadSmtpStatus() | L877 | SMTP | 加载SMTP配置状态 |
| updateSmtpStatusBadge() | L884 | SMTP | 更新SMTP状态徽章 |
| startWorkflow() | L898 | 工作流 | 一键获客全流程 |
| loadCRM() | L954 | CRM | 加载CRM列表 |
| openCRMModal() | L981 | CRM | 打开新增/编辑弹窗 |
| closeCRMModal() | L993 | CRM | 关闭弹窗 |
| saveCRMFromModal() | L995 | CRM | 保存客户数据 |
| editCRM() | L1015 | CRM | 编辑客户（加载详情） |
| deleteCRM() | L1033 | CRM | 删除客户 |
| applySmtpPreset() | L1048 | SMTP | 应用邮箱服务商预设 |
| loadSmtpConfig() | L1059 | SMTP | 加载SMTP配置详情 |
| saveSmtpConfig() | L1077 | SMTP | 保存SMTP配置 |
| testSmtpConfig() | L1095 | SMTP | 测试SMTP连接 |
| clearSmtpConfig() | L1102 | SMTP | 清除SMTP配置 |
| loadHistory() | L1108 | 历史 | 加载邮件发送历史 |
| exportToExcel() | L1133 | 导出 | 通用Excel导出函数 |
| flattenCustomer() | L1141 | 导出 | 客户数据扁平化 |
| exportCRMToExcel() | L1155 | 导出 | 导出CRM数据 |
| exportSearchToExcel() | L1165 | 导出 | 导出搜索结果 |
| exportWorkflowToExcel() | L1170 | 导出 | 导出工作流结果 |

### 5.6 初始化 (L1175-L1184)

**DOMContentLoaded 事件:**
- 检查 localStorage 中的 api_key
- 如果有，设置 _authenticated = true
- 切换到已登录UI
- 自动加载: 仪表盘 / SMTP状态 / CRM / 历史记录

---

## 六、示例数据 (SAMPLE_DATA) - L777-L783

用于"一键AI生成"功能的随机示例数据 (5条):

| 公司 | 行业 | 产品 | 联系人 | 邮箱 |
|------|------|------|--------|------|
| Texas Instruments | electronics | semiconductor | John Smith | support@ti.com |
| IKEA | furniture | office chair | Anna Lindberg | partner@ikea.com |
| Inditex | textile | cotton fabric | Pablo Garcia | supply@inditex.com |
| Caterpillar | machinery | hydraulic pump | Mike Johnson | procurement@cat.com |
| Toyota | automotive | brake system | Tanaka San | supplier@toyota.com |

---

## 七、邮件类型清单 (12种)

| 类型值 | 显示名称 | 渐变背景色 |
|--------|---------|-----------|
| standard | 标准开发信 | - |
| personalized | 个性化 | - |
| follow_up | 跟进邮件 | - |
| cold | 冷邮件 | - |
| ai | 🤖 AI合作型 | #667eea → #764ba2 |
| ai_supplier | 🏭 AI供应商型 | #f093fb → #f5576c |
| ai_inquiry | 💰 AI询价型 | #4facfe → #00f2fe |
| ai_product | 📦 AI产品推介 | #43e97b → #38f9d7 |
| ai_invitation | 📨 AI展会邀请 | #fa709a → #fee140 |
| ai_sample | 🎁 AI样品申请 | #a8edea → #fed6e3 |
| ai_agency | 🤝 AI代理招募 | #d299c2 → #fef9d7 |
| ai_followup | 📞 AI跟进型 | #89f7fe → #66a6ff |

---

## 八、API 接口映射

| 前端函数 | 请求方法 | API 路径 | 说明 |
|----------|---------|----------|------|
| loadDashboard() | GET | /api/dashboard/stats | 仪表盘统计 |
| searchCustomers() | POST | /api/customer/search | 客户搜索 |
| batchScoreSearch() | POST | /api/score/batch | 批量评分 |
| crawlWebsite() | POST | /api/crawl/website | 爬取网站 |
| extractContacts() | POST | /api/crawl/extract-contacts | 提取联系方式 |
| scoreCustomer() | POST | /api/score/customer | 单客户评分 |
| generateEmail() | POST | /api/email/generate | 生成邮件 |
| sendEmail() | POST | /api/email/send | 发送邮件 |
| loadHistory() | GET | /api/email/history | 邮件历史 |
| loadCRM() | GET | /api/crm/customers | CRM列表 |
| editCRM() | GET | /api/crm/customers/{id} | 客户详情 |
| saveCRMFromModal() (新增) | POST | /api/crm/customers | 添加客户 |
| saveCRMFromModal() (编辑) | PUT | /api/crm/customers/{id} | 更新客户 |
| deleteCRM() | DELETE | /api/crm/customers/{id} | 删除客户 |
| loadSmtpConfig() | GET | /api/smtp/config | 获取SMTP配置 |
| saveSmtpConfig() | POST | /api/smtp/config | 保存SMTP配置 |
| testSmtpConfig() | POST | /api/smtp/test | 测试SMTP |
| clearSmtpConfig() | DELETE | /api/smtp/config | 清除SMTP |
| startWorkflow() | POST | /api/workflow/full | 一键获客 |

---

## 九、颜色设计系统

### 主色调
- **主色紫蓝**: #667eea
- **主色紫**: #764ba2
- **主渐变**: linear-gradient(135deg, #667eea 0%, #764ba2 100%)

### 功能色
- 成功: #10b981
- 警告: #f59e0b
- 危险/错误: #ef4444
- 信息: #3b82f6

### 中性色
- 最深文字: #1f2937
- 主要文字: #374151
- 次要文字: #4b5563
- 辅助文字: #6b7280
- 占位文字: #9ca3af
- 边框: #d1d5db
- 分割线: #e5e7eb
- 浅灰: #f3f4f6
- 背景灰: #f9fafb
- 页面背景: #f0f2f5

### 客户等级色
- A级: 绿 (#d1fae5 / #065f46)
- B级: 蓝 (#dbeafe / #1e40af)
- C级: 黄 (#fef3c7 / #92400e)
- D级: 灰 (#f3f4f6 / #4b5563)

---

## 十、页面尺寸与间距规范

| 元素 | 圆角 | 间距/内边距 | 字号 |
|------|------|------------|------|
| 卡片 (.card) | 12px | padding 20px, margin-bottom 16px | - |
| 按钮 (.btn) | 8px | padding 7px 16px | 13px |
| 小按钮 (.btn-sm) | - | padding 4px 10px | 12px |
| 输入框 | 8px | padding 9px 12px | 13px |
| 标签徽章 | 12px | padding 3px 10px | 11px |
| 统计卡片 | 12px | padding 20px | - |
| 表格 | - | padding 12px | 13px |
| Tab 项 | - | padding 16px 20px | 14px |

---

**文档完成。所有页面结构、样式、组件、函数、颜色、尺寸等细节均已详细记录。**
