# App 智能体设计文档

> 文档版本：v1.0
> 创建日期：2026-07-18
> 最后更新：2026-07-18

## 1. 项目概述

### 1.1 项目目标
构建一个可控制各种App的智能体，支持抖音等平台的自动化操作（评论、私信、点赞、关注、数据采集等），采用混合架构（协议API为主，UI自动化兜底），提供Web控制面板和命令行两种交互方式。

### 1.2 技术路线
- **协议层为主**：逆向App网络协议，直接调用API，速度快、效率高
- **UI自动化兜底**：处理登录、验证码等协议层无法解决的场景
- **运行环境**：Windows 10 + Android模拟器/真机 + Python技术栈
- **交互方式**：CLI命令行 + Web控制面板

### 1.3 适用范围
- 个人效率工具，仅限个人学习研究使用
- 首版支持抖音平台，预留扩展其他平台的能力

---

## 2. 总体架构

### 2.1 架构风格
模块化单体架构，预留插件化接口。所有模块在同一进程内运行，通过清晰的接口边界解耦。

### 2.2 架构图

```
┌─────────────────────────────────────────────────────────┐
│                     入口层                              │
│  ┌──────────────┐  ┌──────────────┐                    │
│  │   CLI 入口    │  │  Web 控制面板  │                    │
│  └──────┬───────┘  └──────┬───────┘                    │
└─────────┼─────────────────┼────────────────────────────┘
          │                 │
          └────────┬────────┘
                   ▼
┌─────────────────────────────────────────────────────────┐
│                  核心调度层                              │
│  ┌──────────────────────────────────────────────┐       │
│  │           Task Scheduler (任务调度器)         │       │
│  │  - 任务队列管理                               │       │
│  │  - 账号/设备分配                              │       │
│  │  - 失败重试                                  │       │
│  │  - 任务依赖                                  │       │
│  └──────────────────────────────────────────────┘       │
└───────────────────────┬─────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   抖音平台    │ │  快手平台     │ │  小红书平台   │  ...
│  (Douyin)    │ │ (Kuaishou)   │ │ (Xiaohongshu)│
└──────┬───────┘ └──────────────┘ └──────────────┘
       │
       ├─────────────┬─────────────┐
       ▼             ▼             ▼
  ┌─────────┐   ┌─────────┐   ┌─────────┐
  │ 协议API  │   │ UI自动  │   │ 签名算法 │
  │ (API)   │   │ (UI)    │   │ (Crypto)│
  └─────────┘   └─────────┘   └─────────┘
       │             │
       └──────┬──────┘
              ▼
┌─────────────────────────────────────────────────────────┐
│                  基础设施层                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐        │
│  │ 账号管理    │  │ 设备管理    │  │ 数据存储    │        │
│  │ (Account)  │  │  (Device)   │  │  (Storage)  │        │
│  └────────────┘  └────────────┘  └────────────┘        │
│  ┌────────────┐  ┌────────────┐                        │
│  │  日志系统   │  │  代理管理   │                        │
│  │  (Logger)  │  │  (Proxy)    │                        │
│  └────────────┘  └────────────┘                        │
└─────────────────────────────────────────────────────────┘
```

### 2.3 目录结构

```
app-agent/
├── core/                    # 核心引擎
│   ├── __init__.py
│   ├── task_scheduler.py    # 任务调度器
│   ├── task_queue.py        # 任务队列
│   └── workflow.py          # 工作流编排
├── platforms/               # 平台适配层（插件式）
│   ├── __init__.py
│   ├── base.py              # 平台基类
│   └── douyin/              # 抖音平台
│       ├── __init__.py
│       ├── api.py           # 协议API封装
│       ├── ui.py            # UI自动化封装
│       └── crypto.py        # 签名/加密算法
├── devices/                 # 设备管理层
│   ├── __init__.py
│   ├── adb_client.py        # ADB封装
│   └── device_pool.py       # 设备池
├── accounts/                # 账号管理
│   ├── __init__.py
│   ├── account.py           # 账号模型
│   └── cookie_manager.py    # Cookie/Session管理
├── web/                     # Web控制面板
│   ├── api/                 # 后端API (FastAPI)
│   │   ├── __init__.py
│   │   ├── main.py
│   │   └── routers/
│   └── frontend/            # 前端界面 (Vue3)
├── cli/                     # 命令行入口
│   ├── __init__.py
│   └── main.py
├── storage/                 # 数据存储
│   ├── __init__.py
│   ├── db.py                # 数据库封装
│   └── models.py            # 数据模型
├── utils/                   # 工具函数
│   ├── __init__.py
│   ├── logger.py            # 日志
│   └── proxy.py             # 代理管理
├── config/                  # 配置文件
│   └── config.yaml
├── tasks/                   # 预设任务模板
│   ├── comment.yaml
│   ├── follow.yaml
│   └── dm.yaml
├── docs/                    # 文档
│   └── specs/
├── requirements.txt
└── README.md
```

---

## 3. 核心概念与数据模型

### 3.1 任务（Task）

所有操作都抽象为"任务"，任务有统一的数据结构。

**数据模型：**
```python
class Task:
    id: str                     # 唯一ID (UUID)
    type: str                   # 任务类型：comment/follow/like/dm/scrape_user/...
    platform: str               # 平台：douyin/kuaishou/...
    account_id: str             # 使用的账号ID
    params: dict                # 任务参数（JSON，根据类型不同）
    status: str                 # pending/running/completed/failed/cancelled
    result: dict                # 执行结果
    error: str                  # 错误信息
    created_at: datetime
    started_at: datetime
    finished_at: datetime
    retry_count: int            # 重试次数
    parent_task_id: str         # 父任务ID（用于任务依赖）
```

**任务类型列表：**
| 类型 | 说明 | 参数 |
|------|------|------|
| `follow` | 关注用户 | `{user_id}` |
| `unfollow` | 取关用户 | `{user_id}` |
| `like` | 点赞视频 | `{video_id}` |
| `comment` | 评论视频 | `{video_id, content}` |
| `dm` | 发私信 | `{user_id, content}` |
| `scrape_user` | 采集用户信息 | `{user_id}` |
| `scrape_videos` | 采集用户视频列表 | `{user_id, count}` |
| `scrape_comments` | 采集视频评论 | `{video_id, count}` |
| `search_user` | 搜索用户 | `{keyword, count}` |
| `search_video` | 搜索视频 | `{keyword, count}` |
| `batch_follow` | 批量关注 | `{user_ids: []}` |
| `batch_comment` | 批量评论 | `{video_ids: [], content}` |

### 3.2 账号（Account）

```python
class Account:
    id: str                     # 唯一ID
    platform: str               # 平台
    nickname: str               # 昵称
    user_id: str                # 用户ID
    cookie: str                 # 登录Cookie
    device_info: dict           # 设备指纹
    status: str                 # active/banned/expired
    created_at: datetime
    last_used_at: datetime
```

### 3.3 设备（Device）

```python
class Device:
    id: str                     # 唯一ID
    name: str                   # 设备名称
    serial: str                 # ADB序列号
    platform: str               # android/ios
    system_version: str         # 系统版本
    status: str                 # online/offline/busy
    current_task_id: str        # 当前运行的任务ID
    created_at: datetime
```

### 3.4 任务日志（TaskLog）

```python
class TaskLog:
    id: str
    task_id: str
    level: str                  # info/warn/error
    message: str
    created_at: datetime
```

---

## 4. 核心调度层设计

### 4.1 任务调度器（TaskScheduler）

**职责：**
- 接收任务提交，加入任务队列
- 从队列中取出任务，分配账号和设备
- 调用对应平台执行任务
- 管理任务生命周期
- 失败重试（指数退避）
- 任务依赖管理

**核心流程：**
```
任务提交 → 任务队列 → 调度器取出 → 分配账号 → 分配设备
     ↓
  创建平台实例 → 执行任务 → 更新状态 → 记录结果 → 下一个任务
```

**重试策略：**
- 网络错误：最多重试3次，指数退避（1s → 2s → 4s）
- 业务错误（如参数错误）：不重试
- 账号限制错误：暂停该账号，切换其他账号

### 4.2 任务队列（TaskQueue）

基于内存的优先级队列，支持：
- 任务入队/出队
- 按优先级排序
- 取消任务
- 查看队列状态

---

## 5. 平台适配层设计

### 5.1 平台基类（BasePlatform）

所有App平台都继承同一个基类，上层调度器不关心具体平台实现。

**接口定义：**
```python
class BasePlatform:
    """平台基类"""

    # ---- 账号相关 ----
    def login(self, account) -> bool:
        """登录"""
        raise NotImplementedError

    def is_logged_in(self, account) -> bool:
        """检查登录状态"""
        raise NotImplementedError

    # ---- 用户操作 ----
    def follow(self, user_id) -> bool:
        """关注用户"""
        raise NotImplementedError

    def unfollow(self, user_id) -> bool:
        """取关用户"""
        raise NotImplementedError

    def get_user_info(self, user_id) -> dict:
        """获取用户信息"""
        raise NotImplementedError

    # ---- 视频操作 ----
    def like(self, video_id) -> bool:
        """点赞视频"""
        raise NotImplementedError

    def comment(self, video_id, content) -> str:
        """评论视频，返回评论ID"""
        raise NotImplementedError

    def get_video_info(self, video_id) -> dict:
        """获取视频信息"""
        raise NotImplementedError

    # ---- 私信 ----
    def send_dm(self, user_id, content) -> bool:
        """发送私信"""
        raise NotImplementedError

    def get_dm_list(self) -> list:
        """获取私信列表"""
        raise NotImplementedError

    # ---- 搜索 ----
    def search_user(self, keyword, count=20) -> list:
        """搜索用户"""
        raise NotImplementedError

    def search_video(self, keyword, count=20) -> list:
        """搜索视频"""
        raise NotImplementedError

    # ---- 数据采集 ----
    def get_user_videos(self, user_id, count=20) -> list:
        """获取用户视频列表"""
        raise NotImplementedError

    def get_video_comments(self, video_id, count=20) -> list:
        """获取视频评论列表"""
        raise NotImplementedError
```

### 5.2 抖音平台实现

采用**混合模式**：协议API优先，UI自动化兜底。

#### 5.2.1 协议API层（DouyinAPI）

**核心职责：**
- 封装抖音所有API调用
- 自动处理签名（X-Gorgon / X-Khronos / a-bogus）
- 维护Session和Cookie
- 统一错误处理

**请求流程：**
```
构造请求参数 → 生成签名 → 组装请求头 → 发送请求 → 解析响应 → 返回结果
```

**关键API列表（首版实现）：**
| API | 方法 | 说明 |
|-----|------|------|
| `/aweme/v1/commit/follow/user/` | POST | 关注/取关 |
| `/aweme/v1/commit/item/digg/` | POST | 点赞/取消点赞 |
| `/aweme/v1/comment/publish/` | POST | 发表评论 |
| `/aweme/v1/im/send/` | POST | 发送私信 |
| `/aweme/v1/user/profile/other/` | GET | 获取用户信息 |
| `/aweme/v1/aweme/detail/` | GET | 获取视频详情 |
| `/aweme/v1/user/list/` | GET | 搜索用户 |
| `/aweme/v1/search/item/` | GET | 搜索视频 |
| `/aweme/v1/aweme/post/` | GET | 获取用户视频列表 |
| `/aweme/v1/comment/list/` | GET | 获取评论列表 |

**签名模块（crypto.py）：**
- 封装X-Gorgon、X-Khronos、a-bogus等签名算法
- 提供统一的`sign()`接口
- 支持多种算法版本（根据App版本适配）

#### 5.2.2 UI自动化层（DouyinUI）

**核心职责：**
- 处理协议API无法完成的操作
- 登录、验证码、滑块等场景
- 兜底方案，保证可用性

**技术栈：**
- uiautomator2（Android UI自动化）
- ADB（设备控制）

**核心方法：**
```python
class DouyinUI:
    def start_app(self): ...              # 启动抖音
    def go_home(self): ...                # 回到首页
    def search_user(self, keyword): ...   # 搜索用户
    def follow_user(self, user_id): ...   # 关注用户（UI方式）
    def comment_video(self, video_id, content): ...  # 评论视频（UI方式）
    def send_dm(self, user_id, content): ...  # 发私信（UI方式）
    def get_screenshot(self): ...         # 截图
    def dump_ui(self): ...                # 导出UI层级
```

#### 5.2.3 抖音平台入口（DouyinPlatform）

调度API和UI，对外提供统一接口。

```python
class DouyinPlatform(BasePlatform):
    def __init__(self, account, device=None):
        self.api = DouyinAPI(account.cookie, account.device_info)
        self.ui = DouyinUI(device) if device else None
        self.account = account

    def follow(self, user_id) -> bool:
        try:
            return self.api.follow(user_id)
        except ApiNeedUIError:
            if self.ui:
                return self.ui.follow_user(user_id)
            raise
```

---

## 6. 设备管理层设计

### 6.1 ADB客户端（ADBClient）

封装ADB命令，提供Python接口：
- 设备连接/断开
- 安装/卸载App
- 启动/停止App
- 点击/滑动/输入
- 截图/录屏
- 导出UI层级

### 6.2 设备池（DevicePool）

管理多台设备：
- 设备注册/注销
- 设备状态监控
- 空闲设备分配
- 设备负载均衡

---

## 7. 账号管理层设计

### 7.1 账号管理（AccountManager）

- 账号增删改查
- Cookie有效期检查
- 账号状态管理
- 账号分配策略

### 7.2 Cookie管理器（CookieManager）

- Cookie持久化存储
- Cookie有效性验证
- Cookie自动刷新（UI方式）

---

## 8. 数据存储设计

### 8.1 技术选型
- SQLite（轻量，无需额外服务，适合个人工具）
- SQLAlchemy ORM

### 8.2 数据表
- `accounts` - 账号表
- `tasks` - 任务表
- `task_logs` - 任务日志表
- `devices` - 设备表

---

## 9. Web控制面板设计

### 9.1 技术栈
- **后端**：FastAPI + WebSocket
- **前端**：Vue 3 + Element Plus + Vue Router + Pinia

### 9.2 功能模块

| 模块 | 功能说明 |
|------|----------|
| 任务中心 | 任务列表、新建任务、任务详情、任务日志 |
| 账号管理 | 账号列表、添加账号、账号详情、删除账号 |
| 设备管理 | 设备列表、设备详情、截屏、连接管理 |
| 执行统计 | 任务统计、成功率统计、账号使用统计 |
| 系统设置 | 基础配置、代理设置、日志配置 |

### 9.3 API设计（RESTful + WebSocket）

**REST API：**
```
# 任务
GET    /api/tasks              # 获取任务列表
POST   /api/tasks              # 创建任务
GET    /api/tasks/{id}         # 获取任务详情
POST   /api/tasks/{id}/cancel  # 取消任务
POST   /api/tasks/{id}/retry   # 重试任务

# 账号
GET    /api/accounts           # 获取账号列表
POST   /api/accounts           # 添加账号
GET    /api/accounts/{id}      # 获取账号详情
DELETE /api/accounts/{id}      # 删除账号

# 设备
GET    /api/devices            # 获取设备列表
POST   /api/devices/connect    # 连接设备
GET    /api/devices/{id}       # 获取设备详情
GET    /api/devices/{id}/screenshot  # 设备截屏

# 平台
GET    /api/platforms          # 获取支持的平台列表
GET    /api/platforms/{name}/task-types  # 获取平台支持的任务类型
```

**WebSocket：**
- `/ws/tasks` - 任务状态实时推送
- `/ws/logs/{task_id}` - 任务日志实时推送

---

## 10. CLI 命令行设计

### 10.1 技术选型
- Click（Python命令行框架）

### 10.2 命令列表

```bash
# ========== 账号管理 ==========
douyin-agent account list                    # 列出所有账号
douyin-agent account add --cookie "xxx" --platform douyin  # 添加账号
douyin-agent account remove <account_id>     # 删除账号
douyin-agent account show <account_id>       # 查看账号详情

# ========== 任务管理 ==========
douyin-agent task list                       # 列出任务
douyin-agent task create <type> --account <id> --params '{}'  # 创建任务
douyin-agent task run <task_id>              # 运行任务
douyin-agent task cancel <task_id>           # 取消任务
douyin-agent task show <task_id>             # 查看任务详情
douyin-agent task logs <task_id>             # 查看任务日志

# ========== 快速执行（单条命令） ==========
douyin-agent follow <user_id> --account <id>
douyin-agent unfollow <user_id> --account <id>
douyin-agent like <video_id> --account <id>
douyin-agent comment <video_id> --content "..." --account <id>
douyin-agent dm <user_id> --content "..." --account <id>
douyin-agent scrape user <user_id> --account <id>
douyin-agent scrape videos <user_id> --count 20 --account <id>
douyin-agent scrape comments <video_id> --count 50 --account <id>
douyin-agent search user <keyword> --count 20 --account <id>
douyin-agent search video <keyword> --count 20 --account <id>

# ========== 设备管理 ==========
douyin-agent device list                     # 列出设备
douyin-agent device connect <serial>         # 连接设备
douyin-agent device disconnect <device_id>   # 断开设备
douyin-agent device screenshot <device_id>   # 设备截屏
douyin-agent device show <device_id>         # 查看设备详情

# ========== 服务 ==========
douyin-agent web --port 8000                 # 启动Web控制面板
douyin-agent scheduler start                 # 启动任务调度器（后台）
douyin-agent scheduler stop                  # 停止调度器
douyin-agent scheduler status                # 查看调度器状态
```

---

## 11. 配置系统

### 11.1 配置文件（config.yaml）

```yaml
# 系统配置
system:
  log_level: INFO
  log_dir: ./logs
  data_dir: ./data

# 数据库配置
database:
  type: sqlite
  path: ./data/app_agent.db

# 调度器配置
scheduler:
  max_concurrent_tasks: 5
  retry_max_count: 3
  retry_backoff_base: 1

# 代理配置
proxy:
  enabled: false
  http: ""
  https: ""

# 各平台配置
platforms:
  douyin:
    app_package: com.ss.android.ugc.aweme
    api_base_url: https://www.douyin.com
    # 更多抖音配置...

# 设备配置
devices:
  adb_path: adb
  default_device: ""
```

---

## 12. 错误处理

### 12.1 错误分类

| 错误类型 | 说明 | 处理策略 |
|---------|------|----------|
| `NetworkError` | 网络连接失败 | 自动重试 |
| `ApiSignError` | 签名错误 | 刷新签名算法 |
| `ApiAuthError` | 鉴权失败 | 重新登录 |
| `ApiRateLimitError` | 频率限制 | 等待后重试 |
| `ApiNeedUIError` | 需要UI交互 | 切换到UI自动化 |
| `AccountBannedError` | 账号被封 | 标记账号状态，切换账号 |
| `DeviceError` | 设备异常 | 切换设备 |
| `TaskTimeoutError` | 任务超时 | 取消任务 |

### 12.2 统一错误码

所有错误都有统一的错误码和错误信息，方便排查问题。

---

## 13. 里程碑与实现计划

### 阶段一：核心引擎 + 基础框架
- 项目脚手架搭建
- 数据模型和数据库
- 任务调度器核心
- 平台基类定义
- 日志系统
- 配置系统

### 阶段二：抖音平台（UI自动化优先）
- ADB客户端封装
- 设备管理
- 抖音UI自动化（核心操作）
- 账号管理（Cookie管理）
- 验证UI自动化方案可行性

### 阶段三：抖音协议API
- 抓包和协议分析（文档+工具）
- 签名算法逆向（逐步实现）
- 核心API封装
- API + UI混合调度

### 阶段四：CLI命令行
- 账号管理命令
- 任务管理命令
- 快速执行命令
- 设备管理命令
- 服务管理命令

### 阶段五：Web控制面板
- 后端API（FastAPI）
- WebSocket实时推送
- 前端界面（Vue3）
- 任务管理页面
- 账号管理页面
- 设备管理页面

---

## 14. 风险与注意事项

### 14.1 技术风险
- **签名算法变更**：抖音可能随时更新签名算法，需要持续维护
- **协议变更**：API接口可能变化，需要及时适配
- **账号安全**：频繁操作可能导致账号被限制或封禁

### 14.2 法律风险
- 本工具仅供个人学习研究使用
- 不得用于商业用途或大规模自动化操作
- 不得用于侵犯他人权益的行为
- 使用本工具产生的一切后果由使用者承担

### 14.3 建议
- 使用小号测试，不要用主账号
- 控制操作频率，模拟人类行为
- 定期备份账号数据
- 关注平台规则变化
