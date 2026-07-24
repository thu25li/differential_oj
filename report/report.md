# differential_oj 实验报告

## 1. 项目概述

### 1.1 项目目标

实现一个基于 FastAPI 的 Online Judge 系统，支持用户注册登录、题目管理、Python 代码提交、异步评测、状态机管理、评测日志、备份恢复和代码相似度检测。

### 1.2 已完成功能

**基础模块（30 分）**：

| Step | 模块 | 分值 | 状态 |
|---|---|---|---|
| 1 | 题目管理（CRUD + 字段校验 + 隐藏测试点） | 4 | ✅ |
| 2 | Python 自动评测（AC/WA/RE/TLE/SE） | 4 | ✅ |
| 3 | 用户与权限（Cookie Session + bcrypt） | 4 | ✅ |
| 4 | 提交与状态管理（异步评测 + 状态机） | 4 | ✅ |
| 5 | 评测日志（脱敏 + 截断 + 审计） | 4 | ✅ |
| 6 | 数据持久化、备份与恢复 | 4 | ✅ |
| 7 | 前端交互 | 6 | ✅ |

**进阶模块（5 分）**：

| Adv | 模块 | 状态 |
|---|---|---|
| 3 | 代码相似度检测（AST + difflib） | ✅ |

**其他（10 分）**：代码规范与自动化测试（5 分）+ 实验报告（5 分）。

### 1.3 未完成功能

- Adv 1 Special Judge（未选做）
- Adv 2 安全隔离（Docker/cgroups，未选做）
- 内存限制（MLE）：基础模块未要求，`memory_limit` 字段仅保存不强制

### 1.4 持久化方式

SQLite，WAL 模式，启用外键约束。所有 8 张表见 `app/schema.sql`。

### 1.5 进阶模块

完成 Adv 3 代码相似度检测。算法基于 AST 归一化 + difflib SequenceMatcher，详见第 4 节。

---

## 2. 系统架构

### 2.1 分层架构

```
┌─────────────────────────────────────────────────┐
│  Frontend Layer  (HTML + CSS + JS, Jinja2)      │
│  templates/ + static/                           │
└─────────────────────────────────────────────────┘
                        ↓ HTTP /api/*
┌─────────────────────────────────────────────────┐
│  Router Layer  (app/routers/)                   │
│  auth, problems, users, submissions,            │
│  logs, admin, similarity, pages                 │
└─────────────────────────────────────────────────┘
                        ↓ 调用
┌─────────────────────────────────────────────────┐
│  Service Layer  (app/services/)                 │
│  auth_service, problem_service, user_service,   │
│  submission_service, log_service,               │
│  backup_service, similarity_service             │
└─────────────────────────────────────────────────┘
                        ↓ 调用
┌─────────────────────────────────────────────────┐
│  Repository Layer  (app/repositories/)          │
│  user, problem, submission,                     │
│  case_log, audit_log, backup, similarity        │
└─────────────────────────────────────────────────┘
                        ↓ SQL
┌─────────────────────────────────────────────────┐
│  SQLite (data/oj.db, WAL mode)                  │
└─────────────────────────────────────────────────┘

独立组件：
┌─────────────────────────────────────────────────┐
│  Judge Layer  (app/judge/)                      │
│  comparator.py  输出规范化比较                  │
│  runner.py      异步子进程执行                  │
│  judge.py       多测试点编排                    │
└─────────────────────────────────────────────────┘
```

### 2.2 路由层

每个业务模块对应一个 router 文件，仅负责：

- HTTP 参数解析（Query、Body、Path）
- 权限依赖注入（`Depends(require_*)`）
- 调用 service 层
- 构造统一响应（`ok` / `created` / `accepted`）

不写业务逻辑。

### 2.3 业务层

`services/` 下的类负责：

- 字段校验和错误码映射（404/409/422/500）
- 调用仓库层
- 调用评测器
- 写审计日志

### 2.4 数据访问层

`repositories/` 下的类封装 SQLite 操作：

- 所有 SQL 集中在此层
- 返回 dict 而非 Pydantic 模型，由 service 决定如何变形
- 事务通过 `try / commit / except rollback` 保证

### 2.5 评测层

独立于分层架构，因为不访问数据库，只接收源码和测试点返回结果：

- `comparator`：纯函数，按文档 6 条规则规范化输出后比较
- `runner`：用 `asyncio.create_subprocess_exec` 在独立子进程跑学生代码，超时 kill
- `judge`：编排多测试点，按优先级 `AC < SE < TLE < RE < WA` 聚合

### 2.6 日志层

日志分两类：

- `case_logs`：测试点级日志，存原始 input/stdout/stderr/expected_output（持久化前截断到 4000 字符）
- `audit_logs`：审计日志，6 种动作（VIEW_FULL_JUDGE_LOG / REJUDGE_SUBMISSION / UPDATE_USER_ROLE / DISABLE_USER / CREATE_BACKUP / RESTORE_BACKUP）

日志可见性由 `app/utils/log_views.py` 的 `to_student_log_view` 和 `to_teacher_log_view` 控制。

### 2.7 前端层

原生 HTML + CSS + JS（无框架），由 FastAPI 同源提供服务：

- `app/templates/*.html`：Jinja2 模板（base.html 共用布局）
- `app/static/css/style.css`：基础样式（含 AC/WA/RE/TLE/SE 等 badge）
- `app/static/js/api.js`：fetch 封装（`credentials: 'same-origin'` 保证 Cookie 携带）
- `app/static/js/auth.js`：登录/登出 + 自动渲染导航栏 + requireLogin/requireRole

所有数据来自 `/api/*` 接口，无写死数据。

---

## 3. 数据设计

### 3.1 SQLite 表结构（共 8 张）

详见 `app/schema.sql`。

#### users（用户表）

| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT PK | UUID |
| username | TEXT UNIQUE | 3-32 字符 |
| password_hash | TEXT | bcrypt 哈希 |
| role | TEXT CHECK | student / teacher / admin |
| is_active | INTEGER | 0 或 1 |
| created_at, updated_at | TEXT | ISO 8601 UTC |

#### problems（题目表）

| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT PK | 1-32 字符，全局唯一 |
| title | TEXT | 1-100 字符 |
| description, input_description, output_description | TEXT | 非空 |
| samples | TEXT | JSON 数组字符串 |
| constraints | TEXT | 可空 |
| time_limit | REAL | 秒 |
| memory_limit | INTEGER | MB |
| difficulty | TEXT CHECK | easy / medium / hard |
| tags | TEXT | JSON 数组字符串 |

#### test_cases（测试点表）

`UNIQUE(problem_id, case_id)` 保证题内唯一。`ON DELETE CASCADE` 跟随题目删除（属题目配置）。

#### submissions（提交记录表）

`problem_id` **不加外键**，因为文档要求"题目被删后历史提交保留原 problem_id"。

字段 `status`（pending/running/finished/failed）和 `result`（AC/WA/RE/TLE/SE）有 CHECK 约束。

#### case_logs（测试点级日志）

存 14 个字段：submission_id、case_id、result、score、time_used、memory_used、exit_code、input_data、stdout、stderr、expected_output、message、is_hidden、created_at。

不加外键，保证题目/测试点被删后日志仍可查。

#### audit_logs（审计日志）

`action` 字段有 CHECK 约束，限定 6 种动作。

#### backup_records（备份记录）

记录 backup_id、创建时间、文件数、大小、manifest 路径。

#### similarity_reports（相似度报告，Adv 3）

`similarity` 字段有 CHECK 约束 `0 ≤ similarity ≤ 1`。

### 3.2 索引

为高频筛选字段建索引：

- `idx_sub_user/problem/status/created`（提交列表筛选）
- `idx_case_log_sub`（按提交查日志）
- `idx_audit_operator/target/action/created`（审计日志筛选）
- `idx_sim_problem`（按题目查相似度报告）

---

## 4. 核心实现

### 4.1 异步评测

`submission_service.create` 创建 pending 提交后，**不 await** 直接调度后台任务：

```python
def _schedule_judging(self, submission_id: str) -> None:
    task = asyncio.create_task(self._run_judging(submission_id))
    _pending_tasks.add(task)
    task.add_done_callback(_pending_tasks.discard)
```

`_run_judging` 在子任务里执行：

1. `pending → running`，写 `started_at`
2. 取题目 + 测试点
3. 调 `judge.judge_submission(source_code, test_cases, time_limit)`
4. `running → finished/failed`，写 `result/score/total_time/finished_at`
5. 持久化每个测试点的 case_log（input/stdout/stderr/expected_output 已截断到 4000 字符）

POST 接口立即返回 202 + `submission_id`，不阻塞。

### 4.2 学生代码运行与终止

`app/judge/runner.py` 用 `asyncio.create_subprocess_exec` 启动独立 Python 子进程：

```python
proc = await asyncio.create_subprocess_exec(
    sys.executable, str(code_path),
    stdin=PIPE, stdout=PIPE, stderr=PIPE,
)
try:
    stdout, stderr = await asyncio.wait_for(
        proc.communicate(input=stdin_data.encode("utf-8")),
        timeout=time_limit,
    )
except asyncio.TimeoutError:
    await _kill_proc(proc)   # 立即 kill
    return CaseResult(result="TLE", ...)
```

- 禁用 `eval()` / `exec()`
- 临时目录：`tempfile.gettempdir() / oj_submissions / <uuid32>`
- 评测结束 `cleanup_submission_dir` 删除整个目录
- 学生代码输出非 UTF-8 → 当前测试点 RE

### 4.3 五种评测结果判定

#### AC / WA

`app/judge/comparator.py` 按文档 6 条规则规范化后比较：

1. `\r\n` 和 `\r` 统一转为 `\n`
2. 删除行末空格和制表符（`rstrip(" \t")`）
3. 删除文末多余空行
4. 不忽略行首空格
5. 不忽略行内空格
6. 不允许额外提示语（完全字符串匹配自然保证）

#### RE

- 非零退出码 → RE
- 输出非 UTF-8 → RE

#### TLE

`asyncio.wait_for` 抛 `TimeoutError` → kill 子进程 → TLE

#### SE

- 子进程 spawn 失败 → SE
- `proc.communicate` 抛其他异常 → SE
- 整体评测异常被 service 兜底捕获 → SE + status=failed

### 4.4 最终结果聚合

`judge._aggregate` 严格按文档优先级：

```
all AC         → AC
any SE         → SE
any TLE        → TLE
any RE         → RE
else           → WA
```

### 4.5 提交状态机

`submission_repository.update_status` 和 `update_result` 强制只能走以下路径：

```
pending → running → finished    （result = AC/WA/RE/TLE）
pending → running → failed      （result = SE）
pending → failed                （评测启动前致命错误）
```

`update_result` 根据 result 自动决定 status：result=SE → status=failed；其他 → status=finished。

### 4.6 权限校验

依赖链 `app/utils/auth.py`：

```
get_current_user          # 读 session，查 DB，校验 is_active
    ↓
require_active            # 任何已登录启用用户
    ↓
require_teacher_or_admin  # role ∈ {teacher, admin}
    ↓
require_admin             # role == admin
```

每层都 `raise` 对应错误（401/403），由全局 `OJError` 异常处理器转换为统一响应格式。

**前后端双重校验**：

- 前端 JS：`requireRole(...)` 不符时显示提示
- 后端路由：`Depends(require_*)` 强制校验，绝不依赖前端

### 4.7 隐藏测试点保护

学生查询题目详情时，service 层根据角色返回不同 schema：

```python
include_test_cases = user["role"] in ("teacher", "admin")
```

学生拿到的是 `ProblemPublic`（不含 test_cases），教师/管理员拿到的是 `ProblemFull`。

学生查询测试点日志时，service 用 `to_student_log_view` 进一步过滤：

- 隐藏测试点：完全剥离 input_data / stdout / expected_output
- 公开测试点：保留 stdout 和 expected_output（学生可对照输出）
- 所有测试点：stderr 经过 `sanitize_error_message` 脱敏绝对路径

### 4.8 日志脱敏

`app/utils/log_views.py` 的 `sanitize_error_message`：

```python
_TEMP_PATH_PATTERN = re.compile(
    r"(?:[A-Za-z]:[\\/]|[\\/])(?:[^\s/\\]+[\\/])*[0-9a-fA-F]{32}[\\/]main\.py"
)
return _TEMP_PATH_PATTERN.sub("<submission>/main.py", text)
```

匹配 Linux（`/tmp/oj_submissions/<32hex>/main.py`）和 Windows（`C:\...\oj_submissions\<32hex>\main.py`）路径，统一替换为 `<submission>/main.py`。

### 4.9 持久化与备份恢复

#### 备份

1. `PRAGMA wal_checkpoint(TRUNCATE)` 刷 WAL 到主文件
2. `sqlite3.connect.backup()` API 一致性快照到 `data/backups/<id>/oj.db`
3. 写 `manifest.json`：`{backup_id, created_at, storage_type: "sqlite", files: ["oj.db"], total_size_bytes}`
4. 写 `backup_records` 表
5. 写 `CREATE_BACKUP` 审计

#### 恢复

1. 校验 backup_id 存在
2. 校验 `manifest.json` 可解析且字段完整 → 失败返 400
3. 校验 `oj.db` 文件存在 → 失败返 400
4. **安全副本**：当前 DB 复制到 `.db.safety`
5. `close_database()` → 替换文件 → `init_database()`
6. 任何异常 → 从安全副本回滚 → `init_database()` → 抛 SystemError
7. 写 `RESTORE_BACKUP` 审计

**关键不变量**：损坏的备份（manifest 损坏或 DB 缺失）在**替换之前**就被拒绝，当前数据绝不会破坏。

### 4.10 Adv 3：代码相似度检测

#### 算法

```python
def normalize_code(source: str) -> str:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Name): node.id = "VAR"
        elif isinstance(node, ast.FunctionDef): node.name = "FUNC"
        elif isinstance(node, ast.ClassDef): node.name = "CLASS"
        elif isinstance(node, ast.arg): node.arg = "ARG"
        elif isinstance(node, ast.keyword): node.arg = "KW"
    return ast.dump(tree, annotate_fields=False, include_attributes=False)

def compute_similarity(a: str, b: str) -> float:
    na, nb = normalize_code(a), normalize_code(b)
    if not na or not nb: return 0.0
    return difflib.SequenceMatcher(None, na, nb).ratio()
```

#### 满足文档 6 条要求

| 要求 | 实现 |
|---|---|
| 删除空行和注释 | `ast.parse` 自动忽略 |
| Python 代码 AST 分析 | `ast.parse` + `ast.dump` |
| 降低变量名影响 | 所有 Name/FunctionDef/ClassDef/arg/keyword 名称归一化 |
| 计算 0-1 相似度 | `SequenceMatcher.ratio()` |
| 输出超阈值对 | 默认 0.7，可通过 `OJ_SIMILARITY_THRESHOLD` 配置 |
| 保存报告 | 写入 `similarity_reports` 表，覆盖式重建 |

**仅给出疑似相似结果，不自动标记作弊**——返回的是 `pairs`（提交对）+ 相似度分数，由教师人工判断。

---

## 5. API 说明

### 5.1 认证

| 方法 | 路径 | 权限 | 说明 |
|---|---|---|---|
| POST | `/api/auth/register` | 公开 | 注册，默认 role=student |
| POST | `/api/auth/login` | 公开 | 登录，写入 session |
| POST | `/api/auth/logout` | 公开 | 登出，清 session |
| GET | `/api/auth/me` | 已登录 | 当前用户信息 |

错误码：注册 409（用户名重复）/422（字段不合规）；登录 401（凭证错）/403（被禁用）。

### 5.2 用户

| 方法 | 路径 | 权限 | 说明 |
|---|---|---|---|
| GET | `/api/users` | admin | 分页列表 |
| GET | `/api/users/{id}` | admin | 用户详情 |
| PUT | `/api/users/{id}` | admin | 修改 role / is_active |

错误码：404（用户不存在）/400（禁用自己）/403（非 admin）。

### 5.3 题目

| 方法 | 路径 | 权限 | 说明 |
|---|---|---|---|
| GET | `/api/problems` | 已登录 | 分页列表（不含 test_cases） |
| GET | `/api/problems/{id}` | 已登录 | 详情（学生不含 test_cases） |
| POST | `/api/problems` | teacher/admin | 创建 |
| PUT | `/api/problems/{id}` | teacher/admin | 修改（id 不可改） |
| DELETE | `/api/problems/{id}` | teacher/admin | 删除（保留历史提交） |

错误码：404（不存在）/409（id 重复）/422（字段或分值≠100）/403（学生越权）。

### 5.4 提交

| 方法 | 路径 | 权限 | 说明 |
|---|---|---|---|
| POST | `/api/submissions` | 已登录 | 创建提交，返回 202 |
| GET | `/api/submissions` | 已登录 | 学生只查自己；teacher/admin 全部 |
| GET | `/api/submissions/{id}` | 已登录 | 详情（学生只查自己） |
| POST | `/api/submissions/{id}/rejudge` | teacher/admin | 重置 + 重测 + 审计 |

错误码：404（题目/提交不存在）/422（空代码或字段错）/409（重测非 finished/failed 状态）/403（学生越权）。

### 5.5 日志

| 方法 | 路径 | 权限 | 说明 |
|---|---|---|---|
| GET | `/api/submissions/{id}/logs` | 已登录 | 学生视图（脱敏）/ 教师视图（完整） |
| GET | `/api/logs` | teacher/admin | 多维筛选 + 分页 |
| GET | `/api/audit-logs` | admin | 多维筛选 + 分页 |

教师查看 `/api/submissions/{id}/logs` 自动写 `VIEW_FULL_JUDGE_LOG` 审计。

### 5.6 备份

| 方法 | 路径 | 权限 | 说明 |
|---|---|---|---|
| POST | `/api/admin/backups` | admin | 创建备份，201 |
| GET | `/api/admin/backups` | admin | 列表 |
| POST | `/api/admin/backups/{id}/restore` | admin | 恢复 |

错误码：404（备份不存在）/400（manifest 损坏或 DB 缺失）/500（恢复失败但已回滚）。

### 5.7 相似度（Adv 3）

| 方法 | 路径 | 权限 | 说明 |
|---|---|---|---|
| POST | `/api/problems/{id}/similarity-check` | teacher/admin | 触发查重 |
| GET | `/api/problems/{id}/similarity-reports` | teacher/admin | 查看报告 |

---

## 6. 测试结果

### 6.1 总数

`python -m pytest` 共 **199 个测试**，全部 PASSED。

### 6.2 按模块分布

| 模块 | 测试文件 | 测试数 |
|---|---|---|
| Utils 基础 | `test_utils_basic.py` | 3 |
| 问题模型 | `test_problem_models.py` | 11 |
| 题目仓库 | `test_problem_repository.py` | 8 |
| 题目 API | `test_problems_api.py` | 13 |
| 比较器 | `test_judge_comparator.py` | 18 |
| 子进程执行器 | `test_judge_runner.py` | 8 |
| 评测主流程 | `test_judge_judge.py` | 11 |
| 用户模型 | `test_user_models.py` | 7 |
| 用户仓库 | `test_user_repository.py` | 10 |
| 认证 API | `test_auth_api.py` | 11 |
| 用户管理 API | `test_users_api.py` | 13 |
| 提交仓库 | `test_submission_repository.py` | 10 |
| 提交 API | `test_submissions_api.py` | 18 |
| 测试点日志仓库 | `test_case_log_repository.py` | 8 |
| 日志视图 | `test_log_views.py` | 11 |
| 日志 API | `test_logs_api.py` | 14 |
| 备份 API | `test_backups_api.py` | 14 |
| 相似度 | `test_similarity.py` | 11 |

### 6.3 关键场景覆盖

| 文档验收项 | 测试 |
|---|---|
| AC/WA/RE/TLE/SE 五种结果 | `test_judge_runner.py` + `test_submissions_api.py` |
| 权限三角色 | `test_*_api.py::test_*_cannot_*_403` 系列 |
| 隐藏测试点不可见 | `test_problems_api.py::test_get_detail_as_student_excludes_test_cases` + `test_logs_api.py::test_student_view_hidden_case_*` |
| 状态流转 | `test_submissions_api.py::test_submission_judged_*` 系列 |
| 日志脱敏（路径替换） | `test_log_views.py::test_sanitize_linux_path` + `test_sanitize_windows_path` |
| 重启持久化 | `test_backups_api.py::test_restart_persists_data` |
| 备份恢复 | `test_backups_api.py::test_backup_restore_reverts_data` |
| 损坏备份不破坏当前 | `test_backups_api.py::test_backup_restore_corrupted_manifest_preserves_current` 等 3 个 |
| 代码相似度 | `test_similarity.py::test_*` 系列 |

---

## 7. 问题与解决过程

### 7.1 Windows conda 启动器路径错位

**问题**：在 conda 环境 `oj` 里执行 `pytest`，报错：

```
Fatal error in launcher: Unable to create process using
'"D:\miniconda3\envs\oi\python.exe"  "D:\miniconda3\envs\oj\Scripts\pytest.exe"'
```

`pytest.exe` 启动器内部硬编码了**另一个**环境（`oi`）的 Python 路径，无法找到正确的解释器。

**排查**：Windows 下 pip 为每个 console_scripts 入口生成 `.exe` 包装器，包装器内部嵌入了创建时的 Python 路径。可能因为之前建过同名/类似环境，pip 缓存或某次 `--force-reinstall` 时 PATH 串了。

**解决**：

- 短期：改用 `python -m pytest`，绕开启动器，直接用当前激活环境的 Python 解释器加载 pytest 模块。这是 Python 官方推荐的写法，跨平台、不踩坑。
- 长期：`pip install --force-reinstall --no-deps pytest` 重建启动器。README 写明测试命令用 `python -m pytest` 而非 `pytest`。

### 7.2 模块顶部 `from app.database import DB_PATH` 被 monkey-patch 失效

**问题**：备份恢复测试 `test_backup_restore_reverts_data` 一直失败——恢复后查询数据仍是空。

**排查**：`app/services/backup_service.py` 顶部用 `from app.database import DB_PATH` 导入 `DB_PATH`。这相当于**绑定了导入时的值**。测试 fixture 通过 `db_module.DB_PATH = temp_path` monkey-patch，但 backup_service 里仍是原始 `data/oj.db`。

恢复流程因此把文件写错位置：测试期望临时 DB 被替换，实际生产 DB 被替换，临时 DB 没动，后续查询还读临时 DB 的旧内容。

**解决**：把 backup_service 改成动态访问：

```python
from app import database as db_module
# 用 db_module.DB_PATH 而非 DB_PATH
safety_path = db_module.DB_PATH.with_suffix(".db.safety")
```

每次调用都从模块读取当前值，monkey-patch 立即生效。

**反思**：Python 的 `from module import NAME` 是值绑定，`import module` 是模块引用。需要可变的全局状态时，必须用后者。测试文件也照同样方式改了一遍。

### 7.3 asyncio.create_task 引用被 GC

**问题**：早期版本 `_run_judging` 调度后偶发不执行，没有报错也没有结果。

**排查**：`asyncio.create_task(coro)` 返回的 Task 对象如果没有引用，Python 垃圾回收可能中途回收掉，task 被取消但不抛错。

**解决**：

```python
_pending_tasks: set = set()

def _schedule_judging(self, submission_id: str) -> None:
    task = asyncio.create_task(self._run_judging(submission_id))
    _pending_tasks.add(task)
    task.add_done_callback(_pending_tasks.discard)
```

模块级 `set` 持有引用，任务完成时通过 callback 自动清理。

### 7.4 学生看测试点日志时的字段脱敏

**问题**：初版直接把 `case_logs` 表的内容返回给学生，隐藏测试点的 input/expected_output 全暴露。

**排查**：文档明确要求"学生不能看到隐藏测试点的输入和标准输出"。需要按角色变形响应。

**解决**：写视图函数 `app/utils/log_views.py`：

- `to_student_log_view`：隐藏测试点剥离 input/stdout/expected_output，仅保留 case_id/result/score/time_used/message/stderr
- 公开测试点：保留 stdout 和 expected_output（学生可对照输出）
- 所有 stderr 经 `sanitize_error_message` 替换绝对路径
- 教师视图 `to_teacher_log_view`：全字段（路径不脱敏，截断已在持久化前完成）

学生哪怕用 curl 直接调 API，也拿不到隐藏测试点字段。

---

## 8. AI 工具使用说明

### 8.1 使用的工具

- Claude Code（接入GLM-5.2API），但是下面的工作都是在ai指导我手敲的，并不是ai直接生成（README.md和本报告除外）

### 8.2 AI 参与的工作

| 类型 | 范围 |
|---|---|
| 架构设计 | 教我学习FASTAPI、数据库 schema |
| 代码生成 | `tests/` 下的测试、HTML/CSS/JS 前端设置与美化 |
| 调试 | conda 启动器问题、`DB_PATH` monkey-patch 失效、asyncio.create_task GC、CaseResult 字段补全、Windows 路径正则匹配 |
| 文档 | 本报告、README.md |

### 8.3 如何验证生成内容

1. **运行测试**：每个模块写完立即跑 pytest，确认所有测试通过。199 个测试覆盖 AC/WA/RE/TLE/SE、权限三角色、隐藏测试点、路径脱敏、状态机、备份恢复、相似度等。
2. **手动验收**：用 curl 跑关键流程（创建题目 → 学生提交 → 查看结果 → 教师查日志 → 备份恢复），验证端到端。
3. **逐行审阅**：所有 AI 生成的代码我都看过，发现 4 处问题（见第 7 节）并要求 AI 修正。AI 给的方案我都会判断是否符合文档要求，不符合的返工。
4. **文档对照**：每个 Step 完成后对照文档验收清单逐项核对。

### 8.4 本人修改和确认的部分

- **算法选择**：Adv 3 我要求 AST 归一化（而非 token），AI 实现
- **测试断言**：每条断言我都对照文档要求，确保不是"AI 自己写的假测试"
- **Bug 修复**：第 7 节的 4 个问题都是我和 AI 共同排查定位的，最终方案我确认后实施

### 8.5 我能解释的核心代码

- **比较器 6 条规则**：能逐行解释为什么 `rstrip(" \t")`、为什么不忽略行首空格
- **状态机流转**：能解释为什么 `update_result` 根据 result 决定 status
- **权限依赖链**：能解释 `get_current_user → require_active → require_teacher_or_admin` 的调用顺序
- **备份恢复的安全副本机制**：能解释为什么先复制再替换、为什么 try/except 里还要 rollback
- **AST 相似度算法**：能解释为什么变量名归一化（消除表面差异）、为什么用 difflib 而非编辑距离

---

提交者：李浩永（2025010466）
