-- sqlite schema
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('student', 'teacher', 'admin')),
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS problems (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    input_description TEXT NOT NULL,
    output_description TEXT NOT NULL,
    samples TEXT NOT NULL,
    constraints TEXT,
    time_limit REAL NOT NULL CHECK (time_limit > 0),
    memory_limit INTEGER NOT NULL CHECK (memory_limit > 0),
    difficulty TEXT NOT NULL CHECK (difficulty IN ('easy', 'medium', 'hard')),
    tags TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS test_cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id TEXT NOT NULL,
    problem_id TEXT NOT NULL,
    input TEXT NOT NULL,
    output TEXT NOT NULL,
    score INTEGER NOT NULL CHECK (score >= 0),
    is_hidden INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (problem_id) REFERENCES problems(id) ON DELETE CASCADE,
    UNIQUE (problem_id, case_id)
);
CREATE TABLE IF NOT EXISTS submissions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    problem_id TEXT NOT NULL,
    language TEXT NOT NULL DEFAULT 'python',
    source_code TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'running', 'finished', 'failed')),
    result TEXT CHECK (result IS NULL OR result IN ('AC', 'WA', 'RE', 'TLE', 'SE')),
    score INTEGER NOT NULL DEFAULT 0,
    total_time REAL,
    created_at TEXT NOT NULL,
    started_at TEXT,
    finished_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_sub_user ON submissions(user_id);
CREATE INDEX IF NOT EXISTS idx_sub_problem ON submissions(problem_id);
CREATE INDEX IF NOT EXISTS idx_sub_status ON submissions(status);
CREATE INDEX IF NOT EXISTS idx_sub_created ON submissions(created_at);
CREATE TABLE IF NOT EXISTS case_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    submission_id TEXT NOT NULL,
    case_id TEXT NOT NULL,
    result TEXT NOT NULL CHECK (result IN ('AC', 'WA', 'RE', 'TLE', 'SE')),
    score INTEGER NOT NULL DEFAULT 0,
    time_used REAL NOT NULL,
    memory_used REAL,
    exit_code INTEGER,
    input_data TEXT,
    stdout TEXT,
    stderr TEXT,
    expected_output TEXT,
    message TEXT,
    is_hidden INTEGER NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_case_log_sub ON case_logs(submission_id);
CREATE TABLE IF NOT EXISTS audit_logs (
    id TEXT PRIMARY KEY,
    operator_id TEXT NOT NULL,
    action TEXT NOT NULL CHECK (action IN (
        'VIEW_FULL_JUDGE_LOG',
        'REJUDGE_SUBMISSION',
        'UPDATE_USER_ROLE',
        'DISABLE_USER',
        'CREATE_BACKUP',
        'RESTORE_BACKUP'
    )),
    target_type TEXT NOT NULL,
    target_id TEXT,
    success INTEGER NOT NULL,
    detail TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_audit_operator ON audit_logs(operator_id);
CREATE INDEX IF NOT EXISTS idx_audit_target ON audit_logs(target_id);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_logs(created_at);
CREATE TABLE IF NOT EXISTS backup_records (
    backup_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    storage_type TEXT NOT NULL,
    file_count INTEGER NOT NULL,
    total_size_bytes INTEGER NOT NULL,
    manifest_path TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS similarity_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    problem_id TEXT NOT NULL,
    submission_a TEXT NOT NULL,
    submission_b TEXT NOT NULL,
    similarity REAL NOT NULL CHECK (similarity >= 0 AND similarity <= 1),
    method TEXT NOT NULL DEFAULT 'ast',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sim_problem ON similarity_reports(problem_id);