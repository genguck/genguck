# App 智能体实现计划 - 阶段一：核心引擎 + 基础框架

> **目标：** 搭建项目基础框架，实现核心调度引擎、数据存储、配置系统和日志系统，为后续平台开发打下基础。
>
> **架构：** 模块化单体架构，采用分层设计（入口层 → 调度层 → 平台层 → 基础设施层）
>
> **技术栈：** Python 3.10+ / SQLAlchemy / SQLite / PyYAML / Pydantic

---

## 目录

1. [项目脚手架与依赖](#1-项目脚手架与依赖)
2. [配置系统](#2-配置系统)
3. [日志系统](#3-日志系统)
4. [错误体系](#4-错误体系)
5. [数据模型与数据库](#5-数据模型与数据库)
6. [任务队列](#6-任务队列)
7. [平台基类](#7-平台基类)
8. [任务调度器](#8-任务调度器)
9. [集成测试与冒烟测试](#9-集成测试与冒烟测试)

---

## 1. 项目脚手架与依赖

**Files:**
- Create: `requirements.txt`
- Create: `README.md`
- Create: `__init__.py` 各包初始化文件

- [ ] **Step 1: 创建 requirements.txt**

```text
# ===== 核心依赖 =====
PyYAML>=6.0
pydantic>=2.0,<3.0

# ===== 数据库 =====
SQLAlchemy>=2.0,<3.0
aiosqlite>=0.19.0

# ===== 工具 =====
python-dotenv>=1.0.0
colorlog>=6.7.0

# ===== 测试 =====
pytest>=7.4.0
pytest-asyncio>=0.21.0
```

- [ ] **Step 2: 创建项目目录结构**

```bash
mkdir -p /workspace/app_agent/{core,platforms,devices,accounts,web/api,cli,storage,utils,config,tasks,tests}
touch /workspace/app_agent/{__init__.py,core/__init__.py,platforms/__init__.py,devices/__init__.py,accounts/__init__.py,web/__init__.py,web/api/__init__.py,cli/__init__.py,storage/__init__.py,utils/__init__.py,tests/__init__.py}
```

- [ ] **Step 3: 创建 README.md**

```markdown
# App Agent - App 智能体

一个可以控制各种App的智能体，支持自动化操作（评论、私信、点赞、关注、数据采集等）。

## 特性

- 多平台支持（抖音、快手、小红书等）
- 混合架构：协议API + UI自动化
- Web 控制面板 + CLI 命令行
- 任务调度与队列
- 多账号、多设备管理

## 快速开始

```bash
pip install -r requirements.txt
python -m app_agent.cli.main --help
```

## 项目结构

```
app_agent/
├── core/          # 核心引擎（调度器、任务队列）
├── platforms/     # 平台适配层
├── devices/       # 设备管理
├── accounts/      # 账号管理
├── web/           # Web 控制面板
├── cli/           # 命令行入口
├── storage/       # 数据存储
└── utils/         # 工具函数
```

## 免责声明

本工具仅供个人学习研究使用，不得用于商业用途或违反平台规则。
```

- [ ] **Step 4: 验证目录结构**

```bash
find /workspace/app_agent -type d | sort
```
Expected: 目录结构完整，所有包都有 `__init__.py`

- [ ] **Step 5: 安装依赖**

```bash
cd /workspace && pip install -r requirements.txt
```
Expected: 所有依赖安装成功

---

## 2. 配置系统

**Files:**
- Create: `app_agent/config/config.yaml`
- Create: `app_agent/utils/config.py`
- Test: `tests/test_config.py`

- [ ] **Step 1: 编写测试 - test_config.py**

```python
import os
import tempfile
import pytest
from app_agent.utils.config import load_config, get_config, Config


def test_load_default_config():
    config = load_config()
    assert isinstance(config, Config)
    assert config.system.log_level == "INFO"
    assert config.database.type == "sqlite"
    assert config.scheduler.max_concurrent_tasks == 5


def test_load_custom_config():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("""
system:
  log_level: DEBUG
database:
  path: /tmp/test.db
scheduler:
  max_concurrent_tasks: 10
""")
        tmp_path = f.name

    try:
        config = load_config(tmp_path)
        assert config.system.log_level == "DEBUG"
        assert config.database.path == "/tmp/test.db"
        assert config.scheduler.max_concurrent_tasks == 10
    finally:
        os.unlink(tmp_path)


def test_get_config_singleton():
    config1 = get_config()
    config2 = get_config()
    assert config1 is config2
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd /workspace && python -m pytest tests/test_config.py -v
```
Expected: FAIL with "No module named 'app_agent.utils.config'"

- [ ] **Step 3: 创建默认配置文件 config/config.yaml**

```yaml
system:
  log_level: INFO
  log_dir: ./logs
  data_dir: ./data

database:
  type: sqlite
  path: ./data/app_agent.db

scheduler:
  max_concurrent_tasks: 5
  retry_max_count: 3
  retry_backoff_base: 1

proxy:
  enabled: false
  http: ""
  https: ""

platforms:
  douyin:
    app_package: com.ss.android.ugc.aweme
    api_base_url: https://www.douyin.com

devices:
  adb_path: adb
  default_device: ""
```

- [ ] **Step 4: 实现配置加载器 - utils/config.py**

```python
import os
from pathlib import Path
from typing import Optional
import yaml
from pydantic import BaseModel, Field


class SystemConfig(BaseModel):
    log_level: str = "INFO"
    log_dir: str = "./logs"
    data_dir: str = "./data"


class DatabaseConfig(BaseModel):
    type: str = "sqlite"
    path: str = "./data/app_agent.db"


class SchedulerConfig(BaseModel):
    max_concurrent_tasks: int = 5
    retry_max_count: int = 3
    retry_backoff_base: int = 1


class ProxyConfig(BaseModel):
    enabled: bool = False
    http: str = ""
    https: str = ""


class DouyinPlatformConfig(BaseModel):
    app_package: str = "com.ss.android.ugc.aweme"
    api_base_url: str = "https://www.douyin.com"


class PlatformsConfig(BaseModel):
    douyin: DouyinPlatformConfig = Field(default_factory=DouyinPlatformConfig)


class DevicesConfig(BaseModel):
    adb_path: str = "adb"
    default_device: str = ""


class Config(BaseModel):
    system: SystemConfig = Field(default_factory=SystemConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)
    proxy: ProxyConfig = Field(default_factory=ProxyConfig)
    platforms: PlatformsConfig = Field(default_factory=PlatformsConfig)
    devices: DevicesConfig = Field(default_factory=DevicesConfig)


_config_instance: Optional[Config] = None


def _default_config_path() -> str:
    return str(Path(__file__).parent.parent / "config" / "config.yaml")


def load_config(config_path: Optional[str] = None) -> Config:
    global _config_instance
    path = config_path or _default_config_path()

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        _config_instance = Config(**data)
    else:
        _config_instance = Config()

    return _config_instance


def get_config() -> Config:
    global _config_instance
    if _config_instance is None:
        _config_instance = load_config()
    return _config_instance
```

- [ ] **Step 5: 运行测试确认通过**

```bash
cd /workspace && python -m pytest tests/test_config.py -v
```
Expected: 3 tests passed

---

## 3. 日志系统

**Files:**
- Create: `app_agent/utils/logger.py`
- Test: `tests/test_logger.py`

- [ ] **Step 1: 编写测试 - test_logger.py**

```python
import logging
import pytest
from app_agent.utils.logger import get_logger, setup_logger


def test_get_logger_returns_logger():
    logger = get_logger("test")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "app_agent.test"


def test_get_logger_same_name_same_instance():
    logger1 = get_logger("same")
    logger2 = get_logger("same")
    assert logger1 is logger2


def test_logger_has_handlers_after_setup():
    logger = get_logger("setup_test")
    assert len(logger.handlers) > 0
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd /workspace && python -m pytest tests/test_logger.py -v
```
Expected: FAIL with "No module named 'app_agent.utils.logger'"

- [ ] **Step 3: 实现日志系统 - utils/logger.py**

```python
import logging
import os
from typing import Optional
from datetime import datetime
from app_agent.utils.config import get_config

_loggers = {}


def setup_logger():
    config = get_config()
    log_dir = config.system.log_dir
    os.makedirs(log_dir, exist_ok=True)


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    full_name = f"app_agent.{name}"

    if full_name in _loggers:
        return _loggers[full_name]

    config = get_config()
    log_level = level or config.system.log_level

    logger = logging.getLogger(full_name)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    logger.propagate = False

    if not logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)

        fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        datefmt = "%Y-%m-%d %H:%M:%S"
        formatter = logging.Formatter(fmt, datefmt=datefmt)
        console_handler.setFormatter(formatter)

        logger.addHandler(console_handler)

        log_dir = config.system.log_dir
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
            today = datetime.now().strftime("%Y-%m-%d")
            file_handler = logging.FileHandler(
                os.path.join(log_dir, f"{today}.log"),
                encoding="utf-8"
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    _loggers[full_name] = logger
    return logger
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd /workspace && python -m pytest tests/test_logger.py -v
```
Expected: 3 tests passed

---

## 4. 错误体系

**Files:**
- Create: `app_agent/utils/exceptions.py`
- Test: `tests/test_exceptions.py`

- [ ] **Step 1: 编写测试 - test_exceptions.py**

```python
import pytest
from app_agent.utils.exceptions import (
    AppAgentError,
    NetworkError,
    ApiError,
    ApiAuthError,
    ApiSignError,
    ApiRateLimitError,
    ApiNeedUIError,
    AccountError,
    AccountBannedError,
    DeviceError,
    TaskError,
    TaskTimeoutError,
    TaskNotFoundError,
)


def test_base_error():
    err = AppAgentError("test")
    assert str(err) == "test"
    assert isinstance(err, Exception)


def test_network_error_inheritance():
    err = NetworkError("network down")
    assert isinstance(err, AppAgentError)


def test_api_error_hierarchy():
    auth_err = ApiAuthError("auth failed")
    sign_err = ApiSignError("sign error")
    rate_err = ApiRateLimitError("rate limited")
    ui_err = ApiNeedUIError("need ui")

    assert isinstance(auth_err, ApiError)
    assert isinstance(sign_err, ApiError)
    assert isinstance(rate_err, ApiError)
    assert isinstance(ui_err, ApiError)
    assert isinstance(auth_err, AppAgentError)


def test_account_error_hierarchy():
    banned_err = AccountBannedError("banned")
    assert isinstance(banned_err, AccountError)
    assert isinstance(banned_err, AppAgentError)


def test_task_error_hierarchy():
    timeout_err = TaskTimeoutError("timeout")
    notfound_err = TaskNotFoundError("not found")
    assert isinstance(timeout_err, TaskError)
    assert isinstance(notfound_err, TaskError)
    assert isinstance(timeout_err, AppAgentError)


def test_device_error():
    err = DeviceError("device offline")
    assert isinstance(err, AppAgentError)
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd /workspace && python -m pytest tests/test_exceptions.py -v
```
Expected: FAIL with "No module named 'app_agent.utils.exceptions'"

- [ ] **Step 3: 实现错误体系 - utils/exceptions.py**

```python
class AppAgentError(Exception):
    pass


class NetworkError(AppAgentError):
    pass


class ApiError(AppAgentError):
    def __init__(self, message: str, code: int = 0, response=None):
        super().__init__(message)
        self.code = code
        self.response = response


class ApiAuthError(ApiError):
    pass


class ApiSignError(ApiError):
    pass


class ApiRateLimitError(ApiError):
    pass


class ApiNeedUIError(ApiError):
    pass


class AccountError(AppAgentError):
    pass


class AccountBannedError(AccountError):
    pass


class AccountExpiredError(AccountError):
    pass


class DeviceError(AppAgentError):
    pass


class DeviceOfflineError(DeviceError):
    pass


class TaskError(AppAgentError):
    pass


class TaskNotFoundError(TaskError):
    pass


class TaskTimeoutError(TaskError):
    pass


class TaskCancelledError(TaskError):
    pass


class PlatformError(AppAgentError):
    pass


class PlatformNotSupportedError(PlatformError):
    pass
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd /workspace && python -m pytest tests/test_exceptions.py -v
```
Expected: all tests passed

---

## 5. 数据模型与数据库

**Files:**
- Create: `app_agent/storage/models.py`
- Create: `app_agent/storage/db.py`
- Test: `tests/test_storage.py`

- [ ] **Step 1: 编写测试 - test_storage.py**

```python
import os
import tempfile
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app_agent.storage.models import Base, Task, Account, Device, TaskLog
from app_agent.storage.db import Database, get_db


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = Database(f"sqlite:///{path}")
    db.init_db()
    yield db
    db.close()
    os.unlink(path)


def test_create_tables(temp_db):
    session = temp_db.get_session()
    task = Task(
        id="test-task-1",
        type="follow",
        platform="douyin",
        account_id="acc-1",
        params='{"user_id": "123"}',
        status="pending",
    )
    session.add(task)
    session.commit()

    result = session.query(Task).filter_by(id="test-task-1").first()
    assert result is not None
    assert result.type == "follow"
    assert result.platform == "douyin"
    session.close()


def test_account_model(temp_db):
    session = temp_db.get_session()
    acc = Account(
        id="acc-1",
        platform="douyin",
        nickname="test_user",
        user_id="user_123",
        cookie="test_cookie",
        device_info='{"ua": "test"}',
        status="active",
    )
    session.add(acc)
    session.commit()

    result = session.query(Account).filter_by(id="acc-1").first()
    assert result.nickname == "test_user"
    assert result.status == "active"
    session.close()


def test_device_model(temp_db):
    session = temp_db.get_session()
    dev = Device(
        id="dev-1",
        name="test-device",
        serial="emulator-5554",
        platform="android",
        system_version="12",
        status="online",
    )
    session.add(dev)
    session.commit()

    result = session.query(Device).filter_by(id="dev-1").first()
    assert result.name == "test-device"
    assert result.serial == "emulator-5554"
    session.close()


def test_task_log_model(temp_db):
    session = temp_db.get_session()
    log = TaskLog(
        id="log-1",
        task_id="task-1",
        level="info",
        message="test log message",
    )
    session.add(log)
    session.commit()

    result = session.query(TaskLog).filter_by(task_id="task-1").all()
    assert len(result) == 1
    assert result[0].message == "test log message"
    session.close()


def test_task_status_update(temp_db):
    session = temp_db.get_session()
    task = Task(
        id="test-task-status",
        type="like",
        platform="douyin",
        account_id="acc-1",
        params='{"video_id": "v123"}',
        status="pending",
    )
    session.add(task)
    session.commit()

    task.status = "running"
    task.started_at = datetime.utcnow()
    session.commit()

    result = session.query(Task).filter_by(id="test-task-status").first()
    assert result.status == "running"
    assert result.started_at is not None
    session.close()
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd /workspace && python -m pytest tests/test_storage.py -v
```
Expected: FAIL with import errors

- [ ] **Step 3: 实现数据模型 - storage/models.py**

```python
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def generate_id() -> str:
    return str(uuid.uuid4())


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, default=generate_id)
    type = Column(String(50), nullable=False, index=True)
    platform = Column(String(50), nullable=False, index=True)
    account_id = Column(String(36), nullable=True, index=True)
    params = Column(Text, nullable=False, default="{}")
    status = Column(String(20), nullable=False, default="pending", index=True)
    result = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    retry_count = Column(Integer, default=0)
    parent_task_id = Column(String(36), nullable=True, index=True)

    logs = relationship("TaskLog", back_populates="task", cascade="all, delete-orphan")


class Account(Base):
    __tablename__ = "accounts"

    id = Column(String(36), primary_key=True, default=generate_id)
    platform = Column(String(50), nullable=False, index=True)
    nickname = Column(String(100), nullable=True)
    user_id = Column(String(100), nullable=True, index=True)
    cookie = Column(Text, nullable=True)
    device_info = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="active", index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)


class Device(Base):
    __tablename__ = "devices"

    id = Column(String(36), primary_key=True, default=generate_id)
    name = Column(String(100), nullable=False)
    serial = Column(String(100), nullable=False, unique=True, index=True)
    platform = Column(String(20), nullable=False, default="android")
    system_version = Column(String(50), nullable=True)
    status = Column(String(20), nullable=False, default="offline", index=True)
    current_task_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class TaskLog(Base):
    __tablename__ = "task_logs"

    id = Column(String(36), primary_key=True, default=generate_id)
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=False, index=True)
    level = Column(String(20), nullable=False, default="info")
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    task = relationship("Task", back_populates="logs")
```

- [ ] **Step 4: 实现数据库封装 - storage/db.py**

```python
import os
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app_agent.storage.models import Base
from app_agent.utils.config import get_config
from app_agent.utils.logger import get_logger

logger = get_logger("storage.db")

_db_instance: Optional["Database"] = None


class Database:
    def __init__(self, db_url: Optional[str] = None):
        if db_url is None:
            config = get_config()
            data_dir = config.system.data_dir
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.abspath(config.database.path)
            db_url = f"sqlite:///{db_path}"

        self.db_url = db_url
        self.engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False} if "sqlite" in db_url else {},
        )
        self._SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

    def init_db(self):
        Base.metadata.create_all(bind=self.engine)
        logger.info(f"Database initialized: {self.db_url}")

    def get_session(self) -> Session:
        return self._SessionLocal()

    def close(self):
        self.engine.dispose()


def get_db() -> Database:
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
        _db_instance.init_db()
    return _db_instance
```

- [ ] **Step 5: 运行测试确认通过**

```bash
cd /workspace && python -m pytest tests/test_storage.py -v
```
Expected: all tests passed

---

## 6. 任务队列

**Files:**
- Create: `app_agent/core/task_queue.py`
- Test: `tests/test_task_queue.py`

- [ ] **Step 1: 编写测试 - test_task_queue.py**

```python
import pytest
from app_agent.core.task_queue import TaskQueue, Priority
from app_agent.storage.models import Task


def test_task_queue_add_and_get():
    queue = TaskQueue()
    task1 = Task(id="t1", type="follow", platform="douyin",
                 account_id="a1", params="{}", status="pending")
    task2 = Task(id="t2", type="like", platform="douyin",
                 account_id="a1", params="{}", status="pending")

    queue.add(task1)
    queue.add(task2, priority=Priority.HIGH)

    assert queue.size() == 2

    result = queue.get()
    assert result.id == "t2"
    assert queue.size() == 1

    result = queue.get()
    assert result.id == "t1"
    assert queue.size() == 0


def test_task_queue_empty():
    queue = TaskQueue()
    assert queue.is_empty()
    assert queue.get() is None


def test_task_queue_cancel():
    queue = TaskQueue()
    task = Task(id="cancel-me", type="follow", platform="douyin",
                account_id="a1", params="{}", status="pending")
    queue.add(task)
    assert queue.size() == 1

    result = queue.cancel("cancel-me")
    assert result is True
    assert queue.size() == 0
    assert queue.is_empty()


def test_task_queue_cancel_nonexistent():
    queue = TaskQueue()
    assert queue.cancel("not-exist") is False


def test_task_queue_peek():
    queue = TaskQueue()
    task = Task(id="peek-test", type="follow", platform="douyin",
                account_id="a1", params="{}", status="pending")
    queue.add(task)

    peeked = queue.peek()
    assert peeked.id == "peek-test"
    assert queue.size() == 1


def test_task_queue_priority_order():
    queue = TaskQueue()
    t_low = Task(id="low", type="follow", platform="douyin",
                 account_id="a1", params="{}", status="pending")
    t_normal = Task(id="normal", type="follow", platform="douyin",
                    account_id="a1", params="{}", status="pending")
    t_high = Task(id="high", type="follow", platform="douyin",
                  account_id="a1", params="{}", status="pending")

    queue.add(t_low, priority=Priority.LOW)
    queue.add(t_normal, priority=Priority.NORMAL)
    queue.add(t_high, priority=Priority.HIGH)

    assert queue.get().id == "high"
    assert queue.get().id == "normal"
    assert queue.get().id == "low"


def test_task_queue_clear():
    queue = TaskQueue()
    for i in range(5):
        queue.add(Task(id=f"t{i}", type="follow", platform="douyin",
                       account_id="a1", params="{}", status="pending"))
    assert queue.size() == 5

    queue.clear()
    assert queue.size() == 0
    assert queue.is_empty()
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd /workspace && python -m pytest tests/test_task_queue.py -v
```
Expected: FAIL with import error

- [ ] **Step 3: 实现任务队列 - core/task_queue.py**

```python
import heapq
import threading
from enum import IntEnum
from typing import Optional, List, Tuple
from app_agent.storage.models import Task
from app_agent.utils.logger import get_logger

logger = get_logger("core.task_queue")


class Priority(IntEnum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3


class TaskQueue:
    def __init__(self):
        self._heap: List[Tuple[int, int, str, Task]] = []
        self._counter = 0
        self._lock = threading.Lock()
        self._task_ids = set()

    def add(self, task: Task, priority: Priority = Priority.NORMAL) -> bool:
        with self._lock:
            if task.id in self._task_ids:
                logger.warning(f"Task {task.id} already in queue")
                return False
            self._counter += 1
            heapq.heappush(
                self._heap,
                (-int(priority), self._counter, task.id, task),
            )
            self._task_ids.add(task.id)
            logger.debug(f"Task {task.id} added to queue (priority={priority.name})")
            return True

    def get(self) -> Optional[Task]:
        with self._lock:
            if not self._heap:
                return None
            _, _, task_id, task = heapq.heappop(self._heap)
            self._task_ids.discard(task_id)
            logger.debug(f"Task {task_id} popped from queue")
            return task

    def peek(self) -> Optional[Task]:
        with self._lock:
            if not self._heap:
                return None
            return self._heap[0][3]

    def cancel(self, task_id: str) -> bool:
        with self._lock:
            if task_id not in self._task_ids:
                return False
            new_heap = []
            for item in self._heap:
                if item[2] != task_id:
                    new_heap.append(item)
            heapq.heapify(new_heap)
            self._heap = new_heap
            self._task_ids.discard(task_id)
            logger.debug(f"Task {task_id} cancelled")
            return True

    def size(self) -> int:
        with self._lock:
            return len(self._heap)

    def is_empty(self) -> bool:
        with self._lock:
            return len(self._heap) == 0

    def clear(self):
        with self._lock:
            self._heap.clear()
            self._task_ids.clear()
            logger.debug("Task queue cleared")
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd /workspace && python -m pytest tests/test_task_queue.py -v
```
Expected: all tests passed

---

## 7. 平台基类

**Files:**
- Create: `app_agent/platforms/base.py`
- Create: `app_agent/platforms/registry.py`
- Test: `tests/test_platform_base.py`

- [ ] **Step 1: 编写测试 - test_platform_base.py**

```python
import pytest
from app_agent.platforms.base import BasePlatform
from app_agent.platforms.registry import PlatformRegistry, register_platform


class MockPlatform(BasePlatform):
    platform_name = "mock"

    def __init__(self, account=None, device=None):
        self.account = account
        self.device = device

    def follow(self, user_id: str) -> bool:
        return True

    def unfollow(self, user_id: str) -> bool:
        return True

    def like(self, video_id: str) -> bool:
        return True

    def comment(self, video_id: str, content: str) -> str:
        return "comment_123"

    def send_dm(self, user_id: str, content: str) -> bool:
        return True

    def get_user_info(self, user_id: str) -> dict:
        return {"user_id": user_id, "nickname": "test"}

    def get_video_info(self, video_id: str) -> dict:
        return {"video_id": video_id, "desc": "test"}

    def get_dm_list(self) -> list:
        return []

    def search_user(self, keyword: str, count: int = 20) -> list:
        return []

    def search_video(self, keyword: str, count: int = 20) -> list:
        return []

    def get_user_videos(self, user_id: str, count: int = 20) -> list:
        return []

    def get_video_comments(self, video_id: str, count: int = 20) -> list:
        return []

    def login(self, account) -> bool:
        return True

    def is_logged_in(self, account) -> bool:
        return True


def test_base_platform_cannot_instantiate():
    with pytest.raises(TypeError):
        BasePlatform()


def test_mock_platform_implementation():
    p = MockPlatform()
    assert p.follow("user1") is True
    assert p.like("video1") is True
    assert p.comment("video1", "nice") == "comment_123"
    assert p.send_dm("user1", "hi") is True


def test_platform_registry_register_and_get():
    registry = PlatformRegistry()
    registry.register("mock", MockPlatform)

    assert registry.has("mock")
    platform_cls = registry.get("mock")
    assert platform_cls is MockPlatform


def test_platform_registry_get_unknown():
    registry = PlatformRegistry()
    with pytest.raises(Exception):
        registry.get("unknown")


def test_platform_registry_list():
    registry = PlatformRegistry()
    registry.register("mock1", MockPlatform)
    registry.register("mock2", MockPlatform)

    platforms = registry.list()
    assert "mock1" in platforms
    assert "mock2" in platforms
    assert len(platforms) == 2


def test_register_platform_decorator():
    registry = PlatformRegistry()

    @register_platform("decorated", registry)
    class DecoratedPlatform(MockPlatform):
        platform_name = "decorated"

    assert registry.has("decorated")
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd /workspace && python -m pytest tests/test_platform_base.py -v
```
Expected: FAIL with import error

- [ ] **Step 3: 实现平台基类 - platforms/base.py**

```python
from abc import ABC, abstractmethod
from typing import Optional


class BasePlatform(ABC):
    platform_name: str = ""

    def __init__(self, account=None, device=None):
        self.account = account
        self.device = device

    @abstractmethod
    def login(self, account) -> bool:
        pass

    @abstractmethod
    def is_logged_in(self, account) -> bool:
        pass

    @abstractmethod
    def follow(self, user_id: str) -> bool:
        pass

    @abstractmethod
    def unfollow(self, user_id: str) -> bool:
        pass

    @abstractmethod
    def get_user_info(self, user_id: str) -> dict:
        pass

    @abstractmethod
    def like(self, video_id: str) -> bool:
        pass

    @abstractmethod
    def comment(self, video_id: str, content: str) -> str:
        pass

    @abstractmethod
    def get_video_info(self, video_id: str) -> dict:
        pass

    @abstractmethod
    def send_dm(self, user_id: str, content: str) -> bool:
        pass

    @abstractmethod
    def get_dm_list(self) -> list:
        pass

    @abstractmethod
    def search_user(self, keyword: str, count: int = 20) -> list:
        pass

    @abstractmethod
    def search_video(self, keyword: str, count: int = 20) -> list:
        pass

    @abstractmethod
    def get_user_videos(self, user_id: str, count: int = 20) -> list:
        pass

    @abstractmethod
    def get_video_comments(self, video_id: str, count: int = 20) -> list:
        pass
```

- [ ] **Step 4: 实现平台注册器 - platforms/registry.py**

```python
from typing import Dict, Type, List
from app_agent.platforms.base import BasePlatform
from app_agent.utils.exceptions import PlatformNotSupportedError
from app_agent.utils.logger import get_logger

logger = get_logger("platforms.registry")


class PlatformRegistry:
    def __init__(self):
        self._platforms: Dict[str, Type[BasePlatform]] = {}

    def register(self, name: str, platform_cls: Type[BasePlatform]):
        self._platforms[name] = platform_cls
        logger.info(f"Platform registered: {name}")

    def get(self, name: str) -> Type[BasePlatform]:
        if name not in self._platforms:
            raise PlatformNotSupportedError(f"Platform not supported: {name}")
        return self._platforms[name]

    def has(self, name: str) -> bool:
        return name in self._platforms

    def list(self) -> List[str]:
        return list(self._platforms.keys())


_global_registry = PlatformRegistry()


def get_global_registry() -> PlatformRegistry:
    return _global_registry


def register_platform(name: str, registry: PlatformRegistry = None):
    def decorator(cls):
        reg = registry or _global_registry
        reg.register(name, cls)
        return cls
    return decorator
```

- [ ] **Step 5: 运行测试确认通过**

```bash
cd /workspace && python -m pytest tests/test_platform_base.py -v
```
Expected: all tests passed

---

## 8. 任务调度器

**Files:**
- Create: `app_agent/core/task_scheduler.py`
- Test: `tests/test_task_scheduler.py`

- [ ] **Step 1: 编写测试 - test_task_scheduler.py**

```python
import json
import pytest
from unittest.mock import MagicMock, patch
from app_agent.core.task_scheduler import TaskScheduler
from app_agent.storage.models import Task
from app_agent.platforms.base import BasePlatform


class MockPlatform(BasePlatform):
    platform_name = "mock"

    def __init__(self, account=None, device=None):
        self.account = account
        self.device = device
        self.follow_called = False
        self.like_called = False
        self.comment_called = False
        self.dm_called = False

    def follow(self, user_id: str) -> bool:
        self.follow_called = True
        return True

    def unfollow(self, user_id: str) -> bool:
        return True

    def like(self, video_id: str) -> bool:
        self.like_called = True
        return True

    def comment(self, video_id: str, content: str) -> str:
        self.comment_called = True
        return "cmt_123"

    def send_dm(self, user_id: str, content: str) -> bool:
        self.dm_called = True
        return True

    def get_user_info(self, user_id: str) -> dict:
        return {"user_id": user_id}

    def get_video_info(self, video_id: str) -> dict:
        return {"video_id": video_id}

    def get_dm_list(self) -> list:
        return []

    def search_user(self, keyword: str, count: int = 20) -> list:
        return []

    def search_video(self, keyword: str, count: int = 20) -> list:
        return []

    def get_user_videos(self, user_id: str, count: int = 20) -> list:
        return []

    def get_video_comments(self, video_id: str, count: int = 20) -> list:
        return []

    def login(self, account) -> bool:
        return True

    def is_logged_in(self, account) -> bool:
        return True


@pytest.fixture
def scheduler(temp_db):
    sched = TaskScheduler(db=temp_db)
    sched._get_platform_class = lambda name: MockPlatform
    return sched


def test_scheduler_submit_task(scheduler):
    task = Task(
        id="submit-test",
        type="follow",
        platform="mock",
        account_id="acc1",
        params=json.dumps({"user_id": "u123"}),
    )
    task_id = scheduler.submit_task(task)

    assert task_id == "submit-test"
    assert scheduler.queue.size() == 1


def test_scheduler_execute_follow_task(scheduler, temp_db):
    task = Task(
        id="exec-follow",
        type="follow",
        platform="mock",
        account_id="acc1",
        params=json.dumps({"user_id": "u123"}),
    )
    scheduler.submit_task(task)

    result = scheduler._execute_task(task)

    assert result is True
    session = temp_db.get_session()
    updated = session.query(Task).filter_by(id="exec-follow").first()
    assert updated.status == "completed"
    assert updated.finished_at is not None
    session.close()


def test_scheduler_execute_like_task(scheduler, temp_db):
    task = Task(
        id="exec-like",
        type="like",
        platform="mock",
        account_id="acc1",
        params=json.dumps({"video_id": "v123"}),
    )
    scheduler.submit_task(task)

    result = scheduler._execute_task(task)

    assert result is True


def test_scheduler_execute_comment_task(scheduler, temp_db):
    task = Task(
        id="exec-comment",
        type="comment",
        platform="mock",
        account_id="acc1",
        params=json.dumps({"video_id": "v123", "content": "nice"}),
    )
    scheduler.submit_task(task)

    result = scheduler._execute_task(task)

    assert result is True
    session = temp_db.get_session()
    updated = session.query(Task).filter_by(id="exec-comment").first()
    result_data = json.loads(updated.result)
    assert result_data["comment_id"] == "cmt_123"
    session.close()


def test_scheduler_execute_dm_task(scheduler, temp_db):
    task = Task(
        id="exec-dm",
        type="dm",
        platform="mock",
        account_id="acc1",
        params=json.dumps({"user_id": "u123", "content": "hello"}),
    )
    scheduler.submit_task(task)

    result = scheduler._execute_task(task)

    assert result is True


def test_scheduler_execute_scrape_user_task(scheduler, temp_db):
    task = Task(
        id="exec-scrape",
        type="scrape_user",
        platform="mock",
        account_id="acc1",
        params=json.dumps({"user_id": "u123"}),
    )
    scheduler.submit_task(task)

    result = scheduler._execute_task(task)

    assert result is True


def test_scheduler_task_failure(scheduler, temp_db):
    class FailingPlatform(MockPlatform):
        def follow(self, user_id: str) -> bool:
            raise Exception("follow failed")

    scheduler._get_platform_class = lambda name: FailingPlatform

    task = Task(
        id="fail-test",
        type="follow",
        platform="mock",
        account_id="acc1",
        params=json.dumps({"user_id": "u123"}),
    )
    scheduler.submit_task(task)

    result = scheduler._execute_task(task)

    assert result is False
    session = temp_db.get_session()
    updated = session.query(Task).filter_by(id="fail-test").first()
    assert updated.status == "failed"
    assert "follow failed" in updated.error
    session.close()
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd /workspace && python -m pytest tests/test_task_scheduler.py -v
```
Expected: FAIL with import error

- [ ] **Step 3: 实现任务调度器 - core/task_scheduler.py**

```python
import json
import time
import threading
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app_agent.core.task_queue import TaskQueue, Priority
from app_agent.storage.db import Database, get_db
from app_agent.storage.models import Task, TaskLog, Account
from app_agent.platforms.registry import get_global_registry
from app_agent.utils.logger import get_logger
from app_agent.utils.config import get_config
from app_agent.utils.exceptions import AppAgentError

logger = get_logger("core.scheduler")


class TaskScheduler:
    def __init__(self, db: Optional[Database] = None):
        self.db = db or get_db()
        self.queue = TaskQueue()
        self._running = False
        self._lock = threading.Lock()
        self._active_tasks: Dict[str, threading.Thread] = {}
        self._config = get_config()

    def submit_task(self, task: Task, priority: Priority = Priority.NORMAL) -> str:
        session = self.db.get_session()
        try:
            session.add(task)
            session.commit()
            session.refresh(task)
            task_id = task.id

            self.queue.add(task, priority)
            logger.info(f"Task submitted: {task_id} (type={task.type}, platform={task.platform})")

            self._log_task(task_id, "info", f"Task submitted, type={task.type}")

            return task_id
        finally:
            session.close()

    def start(self):
        with self._lock:
            if self._running:
                logger.warning("Scheduler already running")
                return
            self._running = True
            logger.info("Task scheduler started")

        threading.Thread(target=self._run_loop, daemon=True).start()

    def stop(self):
        with self._lock:
            self._running = False
        logger.info("Task scheduler stopping...")

    def _run_loop(self):
        while self._running:
            try:
                if len(self._active_tasks) < self._config.scheduler.max_concurrent_tasks:
                    task = self.queue.get()
                    if task:
                        self._start_task_thread(task)
                    else:
                        time.sleep(0.5)
                else:
                    time.sleep(0.5)
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                time.sleep(1)

    def _start_task_thread(self, task: Task):
        thread = threading.Thread(
            target=self._execute_task_safe,
            args=(task,),
            daemon=True,
        )
        self._active_tasks[task.id] = thread
        thread.start()

    def _execute_task_safe(self, task: Task):
        try:
            self._execute_task(task)
        except Exception as e:
            logger.error(f"Task {task.id} unexpected error: {e}")
        finally:
            self._active_tasks.pop(task.id, None)

    def _execute_task(self, task: Task) -> bool:
        session = self.db.get_session()
        try:
            task_db = session.query(Task).filter_by(id=task.id).first()
            if not task_db:
                logger.error(f"Task {task.id} not found in database")
                return False

            if task_db.status == "cancelled":
                logger.info(f"Task {task.id} was cancelled, skipping")
                return False

            task_db.status = "running"
            task_db.started_at = datetime.utcnow()
            session.commit()

            self._log_task(task.id, "info", f"Task started, type={task.type}")

            platform = self._create_platform(task_db, session)
            result = self._dispatch_task(platform, task_db)

            task_db.status = "completed"
            task_db.result = json.dumps(result, ensure_ascii=False) if result else "{}"
            task_db.finished_at = datetime.utcnow()
            session.commit()

            self._log_task(task.id, "info", "Task completed successfully")
            logger.info(f"Task {task.id} completed")
            return True

        except Exception as e:
            task_db = session.query(Task).filter_by(id=task.id).first()
            if task_db:
                task_db.status = "failed"
                task_db.error = str(e)
                task_db.finished_at = datetime.utcnow()
                session.commit()

            self._log_task(task.id, "error", f"Task failed: {e}")
            logger.error(f"Task {task.id} failed: {e}")
            return False
        finally:
            session.close()

    def _create_platform(self, task: Task, session: Session):
        registry = get_global_registry()
        platform_cls = registry.get(task.platform)

        account = None
        if task.account_id:
            account = session.query(Account).filter_by(id=task.account_id).first()

        platform = platform_cls(account=account, device=None)
        return platform

    def _dispatch_task(self, platform, task: Task) -> Any:
        params = json.loads(task.params or "{}")
        task_type = task.type

        dispatch_map = {
            "follow": lambda: platform.follow(params["user_id"]),
            "unfollow": lambda: platform.unfollow(params["user_id"]),
            "like": lambda: platform.like(params["video_id"]),
            "comment": lambda: {
                "comment_id": platform.comment(params["video_id"], params["content"])
            },
            "dm": lambda: {"success": platform.send_dm(params["user_id"], params["content"])},
            "scrape_user": lambda: platform.get_user_info(params["user_id"]),
            "scrape_videos": lambda: {
                "videos": platform.get_user_videos(
                    params["user_id"], params.get("count", 20)
                )
            },
            "scrape_comments": lambda: {
                "comments": platform.get_video_comments(
                    params["video_id"], params.get("count", 20)
                )
            },
            "search_user": lambda: {
                "users": platform.search_user(
                    params["keyword"], params.get("count", 20)
                )
            },
            "search_video": lambda: {
                "videos": platform.search_video(
                    params["keyword"], params.get("count", 20)
                )
            },
        }

        if task_type not in dispatch_map:
            raise ValueError(f"Unsupported task type: {task_type}")

        return dispatch_map[task_type]()

    def _log_task(self, task_id: str, level: str, message: str):
        session = self.db.get_session()
        try:
            log = TaskLog(task_id=task_id, level=level, message=message)
            session.add(log)
            session.commit()
        finally:
            session.close()

    def cancel_task(self, task_id: str) -> bool:
        if self.queue.cancel(task_id):
            session = self.db.get_session()
            try:
                task = session.query(Task).filter_by(id=task_id).first()
                if task and task.status == "pending":
                    task.status = "cancelled"
                    session.commit()
                self._log_task(task_id, "info", "Task cancelled")
                return True
            finally:
                session.close()
        return False

    def get_task_status(self, task_id: str) -> Optional[Task]:
        session = self.db.get_session()
        try:
            return session.query(Task).filter_by(id=task_id).first()
        finally:
            session.close()
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd /workspace && python -m pytest tests/test_task_scheduler.py tests/test_storage.py tests/test_task_queue.py tests/test_platform_base.py -v
```
Expected: all tests passed

---

## 9. 集成测试与冒烟测试

**Files:**
- Create: `tests/test_integration.py`
- Modify: `tests/conftest.py`

- [ ] **Step 1: 创建 conftest.py**

```python
import os
import tempfile
import pytest
from app_agent.storage.db import Database
from app_agent.storage.models import Base


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = Database(f"sqlite:///{path}")
    db.init_db()
    yield db
    db.close()
    os.unlink(path)
```

- [ ] **Step 2: 编写集成测试 - test_integration.py**

```python
import json
import pytest
from app_agent.core.task_scheduler import TaskScheduler
from app_agent.storage.models import Task
from app_agent.platforms.base import BasePlatform


class TestPlatform(BasePlatform):
    platform_name = "test"

    def __init__(self, account=None, device=None):
        self.account = account
        self.device = device

    def follow(self, user_id: str) -> bool:
        return True

    def unfollow(self, user_id: str) -> bool:
        return True

    def like(self, video_id: str) -> bool:
        return True

    def comment(self, video_id: str, content: str) -> str:
        return f"cmt_{video_id}"

    def send_dm(self, user_id: str, content: str) -> bool:
        return True

    def get_user_info(self, user_id: str) -> dict:
        return {"user_id": user_id, "nickname": f"user_{user_id}", "followers": 100}

    def get_video_info(self, video_id: str) -> dict:
        return {"video_id": video_id, "desc": "test video"}

    def get_dm_list(self) -> list:
        return []

    def search_user(self, keyword: str, count: int = 20) -> list:
        return [{"user_id": f"{keyword}_{i}", "nickname": f"{keyword}_{i}"} for i in range(count)]

    def search_video(self, keyword: str, count: int = 20) -> list:
        return [{"video_id": f"v_{keyword}_{i}"} for i in range(count)]

    def get_user_videos(self, user_id: str, count: int = 20) -> list:
        return [{"video_id": f"{user_id}_v{i}"} for i in range(count)]

    def get_video_comments(self, video_id: str, count: int = 20) -> list:
        return [{"comment_id": f"c_{i}", "text": f"comment {i}"} for i in range(count)]

    def login(self, account) -> bool:
        return True

    def is_logged_in(self, account) -> bool:
        return True


@pytest.fixture
def integration_scheduler(temp_db):
    from app_agent.platforms.registry import get_global_registry
    registry = get_global_registry()
    if not registry.has("test"):
        registry.register("test", TestPlatform)

    sched = TaskScheduler(db=temp_db)
    return sched


def test_full_follow_workflow(integration_scheduler, temp_db):
    task = Task(
        type="follow",
        platform="test",
        account_id="acc-integration",
        params=json.dumps({"user_id": "user_abc"}),
    )

    task_id = integration_scheduler.submit_task(task)
    assert task_id is not None

    result = integration_scheduler._execute_task(task)
    assert result is True

    session = temp_db.get_session()
    db_task = session.query(Task).filter_by(id=task_id).first()
    assert db_task.status == "completed"
    assert db_task.started_at is not None
    assert db_task.finished_at is not None
    assert len(db_task.logs) > 0
    session.close()


def test_full_scrape_workflow(integration_scheduler, temp_db):
    task = Task(
        type="scrape_user",
        platform="test",
        account_id="acc-integration",
        params=json.dumps({"user_id": "user_xyz"}),
    )

    task_id = integration_scheduler.submit_task(task)
    result = integration_scheduler._execute_task(task)

    assert result is True
    session = temp_db.get_session()
    db_task = session.query(Task).filter_by(id=task_id).first()
    result_data = json.loads(db_task.result)
    assert result_data["user_id"] == "user_xyz"
    assert result_data["nickname"] == "user_user_xyz"
    session.close()


def test_comment_returns_id(integration_scheduler, temp_db):
    task = Task(
        type="comment",
        platform="test",
        account_id="acc-integration",
        params=json.dumps({"video_id": "v_123", "content": "great video!"}),
    )

    task_id = integration_scheduler.submit_task(task)
    result = integration_scheduler._execute_task(task)

    assert result is True
    session = temp_db.get_session()
    db_task = session.query(Task).filter_by(id=task_id).first()
    result_data = json.loads(db_task.result)
    assert result_data["comment_id"] == "cmt_v_123"
    session.close()


def test_search_user_workflow(integration_scheduler, temp_db):
    task = Task(
        type="search_user",
        platform="test",
        account_id="acc-integration",
        params=json.dumps({"keyword": "hello", "count": 5}),
    )

    task_id = integration_scheduler.submit_task(task)
    result = integration_scheduler._execute_task(task)

    assert result is True
    session = temp_db.get_session()
    db_task = session.query(Task).filter_by(id=task_id).first()
    result_data = json.loads(db_task.result)
    assert len(result_data["users"]) == 5
    assert result_data["users"][0]["user_id"] == "hello_0"
    session.close()


def test_task_cancel_before_execution(integration_scheduler, temp_db):
    task = Task(
        type="follow",
        platform="test",
        account_id="acc-integration",
        params=json.dumps({"user_id": "user_cancel"}),
    )

    task_id = integration_scheduler.submit_task(task)
    assert integration_scheduler.queue.size() == 1

    cancelled = integration_scheduler.cancel_task(task_id)
    assert cancelled is True
    assert integration_scheduler.queue.size() == 0

    session = temp_db.get_session()
    db_task = session.query(Task).filter_by(id=task_id).first()
    assert db_task.status == "cancelled"
    session.close()
```

- [ ] **Step 3: 运行全部测试**

```bash
cd /workspace && python -m pytest tests/ -v
```
Expected: all tests passed

- [ ] **Step 4: 手动冒烟测试**

```python
import json
from app_agent.core.task_scheduler import TaskScheduler
from app_agent.storage.db import get_db
from app_agent.storage.models import Task

db = get_db()
scheduler = TaskScheduler(db=db)

# 提交一个测试任务（用test平台）
task = Task(
    type="follow",
    platform="test",
    account_id="smoke-test-acc",
    params=json.dumps({"user_id": "test_user_123"}),
)
task_id = scheduler.submit_task(task)
print(f"Task submitted: {task_id}")

# 手动执行
result = scheduler._execute_task(task)
print(f"Task result: {result}")

# 查看状态
status = scheduler.get_task_status(task_id)
print(f"Task status: {status.status}")
```

Expected: 输出显示任务成功完成，状态为 completed

---

## 阶段一完成检查清单

- [ ] 项目脚手架搭建完成
- [ ] 配置系统可用
- [ ] 日志系统可用
- [ ] 错误体系完整
- [ ] 数据模型定义完成
- [ ] 数据库封装可用
- [ ] 任务队列可用
- [ ] 平台基类与注册器可用
- [ ] 任务调度器核心功能可用
- [ ] 所有单元测试通过
- [ ] 集成测试通过
- [ ] 冒烟测试通过
