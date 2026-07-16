from typing import List, Optional, Tuple
from app.database import get_db
class UserRepository:
    async def create(self, user: dict) -> None:
        db = await get_db()
        try:
            await db.execute(
                """INSERT INTO users
                   (id, username, password_hash, role, is_active, created_at,
updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    user["id"], user["username"], user["password_hash"],
                    user["role"], 1 if user["is_active"] else 0,
                    user["created_at"], user["updated_at"],
                ),
            )
            await db.commit()
        except Exception:
            await db.rollback()
            raise
    async def get_by_id(self, user_id: str) -> Optional[dict]:
        db = await get_db()
        cursor = await db.execute(
            """SELECT id, username, password_hash, role, is_active, created_at,
updated_at
               FROM users WHERE id = ?""",
            (user_id,),
        )
        row = await cursor.fetchone()
        return self._row_to_full(row) if row else None
    async def get_by_username(self, username: str) -> Optional[dict]:
        db = await get_db()
        cursor = await db.execute(
            """SELECT id, username, password_hash, role, is_active, created_at,
updated_at
               FROM users WHERE username = ?""",
            (username,),
        )
        row = await cursor.fetchone()
        return self._row_to_full(row) if row else None
    async def list(self, page: int = 1, page_size: int = 20) -> Tuple[List[dict],
int]:
        db = await get_db()
        offset = (page - 1) * page_size
        cursor = await db.execute(
            """SELECT id, username, role, is_active, created_at, updated_at
               FROM users ORDER BY created_at, id LIMIT ? OFFSET ?""",
            (page_size, offset),
        )
        rows = await cursor.fetchall()
        items = [self._row_to_public(row) for row in rows]
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        total = (await cursor.fetchone())[0]
        return items, total
    async def update(self, user_id: str, updates: dict) -> bool:
        db = await get_db()
        set_parts: List[str] = []
        params: List = []
        if updates.get("role") is not None:
            set_parts.append("role = ?")
            params.append(updates["role"])
        if updates.get("is_active") is not None:
            set_parts.append("is_active = ?")
            params.append(1 if updates["is_active"] else 0)
        if not set_parts:
            return await self.exists(user_id)
        set_parts.append("updated_at = ?")
        params.append(updates["updated_at"])
        params.append(user_id)
        try:
            cursor = await db.execute(
                f"UPDATE users SET {', '.join(set_parts)} WHERE id = ?",
                params,
            )
            if cursor.rowcount == 0:
                await db.rollback()
                return False
            await db.commit()
            return True
        except Exception:
            await db.rollback()
            raise
    async def exists(self, user_id: str) -> bool:
        db = await get_db()
        cursor = await db.execute("SELECT 1 FROM users WHERE id = ?", (user_id,))
        return await cursor.fetchone() is not None
    async def username_exists(self, username: str) -> bool:
        db = await get_db()
        cursor = await db.execute("SELECT 1 FROM users WHERE username = ?",
(username,))
        return await cursor.fetchone() is not None
    async def count_admins(self) -> int:
        db = await get_db()
        cursor = await db.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
        return (await cursor.fetchone())[0]
    @staticmethod
    def _row_to_full(row) -> dict:
        return {
            "id": row["id"],
            "username": row["username"],
            "password_hash": row["password_hash"],
            "role": row["role"],
            "is_active": bool(row["is_active"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
    @staticmethod
    def _row_to_public(row) -> dict:
        return {
            "id": row["id"],
            "username": row["username"],
            "role": row["role"],
            "is_active": bool(row["is_active"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
user_repository = UserRepository()