# Differential OJ

基于 FastAPI 的 Online Judge 系统，支持 Python 代码提交、异步评测、多测试点评测、AC/WA/RE/TLE/SE 识别、用户权限管理、评测日志、备份恢复和代码相似度检测。

## Python 版本

- Python 3.10 或以上

## 安装依赖

推荐使用 conda 环境：

```bash
conda create -n oj python=3.10 -y
conda activate oj
pip install -r requirements.txt
```

## 后端启动命令

```bash
conda activate oj
python -m uvicorn app.main:app
```

默认监听 `http://127.0.0.1:8000`。

> Windows 下不要使用 `uvicorn ... --reload`：`--reload` 会触发 `SelectorEventLoop`，导致 `asyncio.create_subprocess_exec` 评测子进程失败（提交会显示 SE）。直接 `python -m uvicorn app.main:app` 即可。

- API 文档：`http://127.0.0.1:8000/docs`
- 前端首页：`http://127.0.0.1:8000/`

## 测试命令

```bash
conda activate oj
python -m pytest
```

当前共 199 个测试，覆盖：题目 CRUD、Python 评测器、用户权限、提交状态机、日志脱敏、备份恢复、相似度检测。

## 初始管理员账号

首次启动时，系统会自动创建一个默认管理员账号（写入 SQLite 数据库，密码用 bcrypt 哈希）：

- 用户名：`admin`
- 密码：`admin12345`

**生产部署前请通过环境变量覆盖默认值**：

```bash
export OJ_ADMIN_USERNAME=your_admin
export OJ_ADMIN_PASSWORD=your_secure_password
export OJ_SECRET_KEY=your_random_secret_for_session
```

Windows PowerShell：

```powershell
$env:OJ_ADMIN_USERNAME = "your_admin"
$env:OJ_ADMIN_PASSWORD = "your_secure_password"
$env:OJ_SECRET_KEY = "your_random_secret_for_session"
```

## 持久化方式

- **存储类型**：SQLite（WAL 模式，启用外键约束）
- **数据库文件**：`data/oj.db`（首次启动自动创建）
- **备份目录**：`data/backups/<backup_id>/`，每个备份包含 `oj.db` 副本和 `manifest.json`

## 前端启动

前端使用原生 HTML/CSS/JavaScript，由 FastAPI 同源提供服务，无需单独启动。后端启动后直接访问 `http://127.0.0.1:8000/` 即可。

前端代码位置：

- 模板：`app/templates/*.html`
- 静态资源：`app/static/css/` 和 `app/static/js/`

## 功能清单

### 基础模块

- ✅ 用户注册、登录、登出（Cookie Session + bcrypt）
- ✅ 三种角色：student / teacher / admin
- ✅ 题目 CRUD（含字段校验、隐藏测试点、分值=100 校验）
- ✅ Python 代码异步评测（子进程隔离 + 超时 kill）
- ✅ AC / WA / RE / TLE / SE 五种评测结果
- ✅ 多测试点评分（AC 测试点分值之和）
- ✅ 提交状态机（pending → running → finished/failed）
- ✅ 重新评测（写审计日志）
- ✅ 测试点级日志（学生视图脱敏 + 教师视图完整 + 路径替换 + 4000 字符截断）
- ✅ 审计日志（VIEW_FULL_JUDGE_LOG / REJUDGE / UPDATE_USER_ROLE / DISABLE_USER / CREATE_BACKUP / RESTORE_BACKUP）
- ✅ 数据持久化（SQLite）+ 备份 + 恢复（manifest.json 校验、损坏备份不破坏当前数据）
- ✅ 前端：登录、题目列表/详情、代码提交、提交详情轮询、学生提交列表、教师题目管理、管理员备份管理

### 进阶模块

- ✅ **Adv 3 代码相似度检测**：基于 AST 归一化 + difflib 计算相似度，变量名/函数名/类名/参数名全部归一化，输出超阈值对，**仅给出疑似相似结果，不自动标记作弊**

## API 接口概览

所有接口统一前缀 `/api`，响应格式 `{code, message, data}`。详见 `http://127.0.0.1:8000/docs`。

| 模块 | 接口 |
|---|---|
| 认证 | `POST /api/auth/register` `POST /api/auth/login` `POST /api/auth/logout` `GET /api/auth/me` |
| 用户 | `GET /api/users` `GET /api/users/{id}` `PUT /api/users/{id}` |
| 题目 | `GET /api/problems` `GET /api/problems/{id}` `POST /api/problems` `PUT /api/problems/{id}` `DELETE /api/problems/{id}` |
| 提交 | `POST /api/submissions` `GET /api/submissions` `GET /api/submissions/{id}` `POST /api/submissions/{id}/rejudge` |
| 日志 | `GET /api/submissions/{id}/logs` `GET /api/logs` `GET /api/audit-logs` |
| 备份 | `POST /api/admin/backups` `GET /api/admin/backups` `POST /api/admin/backups/{id}/restore` |
| 相似度 | `POST /api/problems/{id}/similarity-check` `GET /api/problems/{id}/similarity-reports` |

## 项目结构

```
differential_oj/
├── app/
│   ├── main.py              # FastAPI 入口，中间件、异常处理器、路由注册
│   ├── database.py          # aiosqlite 连接管理 + 启动时建表 + 初始化 admin
│   ├── schema.sql           # SQLite 表结构定义（8 张表）
│   ├── models/              # Pydantic 模型和枚举
│   ├── routers/             # FastAPI 路由（按模块拆分）
│   ├── services/            # 业务逻辑层
│   ├── repositories/        # SQLite 数据访问层
│   ├── judge/               # 评测器（comparator / runner / judge）
│   ├── utils/               # 工具（认证依赖、错误、时间、ID、密码、日志视图）
│   ├── templates/           # Jinja2 HTML 模板
│   └── static/              # 前端 CSS/JS
├── data/                    # SQLite 文件 + 备份（不提交）
├── tests/                   # pytest 测试套件
├── report/                  # 实验报告
├── requirements.txt
├── pytest.ini
└── README.md
```

## 已知限制

1. **未实现内存限制（MLE）**：`memory_limit` 字段仅保存，不强制；基础模块未要求实现 MLE。
2. **并发评测**：单进程 `asyncio.create_task` 调度，未实现分布式任务队列；不适合高并发场景。
3. **学生代码沙箱**：基础模块仅靠子进程超时和临时目录隔离，未实现 Docker / cgroups / 网络隔离（属 Adv 2 未选做）。
4. **Session 失效**：恢复备份后 Session 不强制失效（文档允许）。
5. **管理员默认密码**：`admin12345` 是占位密码，**生产环境必须通过环境变量覆盖**。
6. **首次相似度检测**：算法是 O(n²) 两两比对，提交数 >100 时会变慢。
7. **代码大小**：单次提交限制 64 KiB。
