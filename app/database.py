import os
from pathlib import Path
from typing import Optional
import aiosqlite
from app.utils.id_gen import generate_uuid
from app.utils.password import hash_password
from app.utils.time import now_utc
DB_PATH = Path("data/oj.db")
SCHEMA_PATH = Path(__file__).parent / "schema.sql"
_conn: Optional[aiosqlite.Connection] = None
async def get_db() -> aiosqlite.Connection:
    if _conn is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return _conn
async def init_database() -> None:
    global _conn
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    _conn = await aiosqlite.connect(str(DB_PATH))
    _conn.row_factory = aiosqlite.Row
    await _conn.execute("PRAGMA foreign_keys = ON")
    await _conn.execute("PRAGMA journal_mode = WAL")
    await _conn.execute("PRAGMA synchronous = NORMAL")
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    await _conn.executescript(schema_sql)
    await _conn.commit()
    await _ensure_admin_account()
async def close_database() -> None:
    global _conn
    if _conn is not None:
        await _conn.close()
        _conn = None
async def _ensure_admin_account() -> None:
    db = _conn
    cursor = await db.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
    count = (await cursor.fetchone())[0]
    if count > 0:
        return
    username = os.environ.get("OJ_ADMIN_USERNAME", "admin")
    password = os.environ.get("OJ_ADMIN_PASSWORD", "admin12345")
    if len(username) < 3 or len(username) > 32:
        raise RuntimeError("OJ_ADMIN_USERNAME must be 3-32 characters")
    if len(password) < 8:
        raise RuntimeError("OJ_ADMIN_PASSWORD must be at least 8 characters")
    ts = now_utc()
    await db.execute(
        """INSERT INTO users
           (id, username, password_hash, role, is_active, created_at, updated_at)
           VALUES (?, ?, ?, 'admin', 1, ?, ?)""",
        (generate_uuid(), username, hash_password(password), ts, ts),
    )
    await db.commit()