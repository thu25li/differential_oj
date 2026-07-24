from typing import List, Optional, Tuple
from app.database import get_db
class AuditLogRepository:
    async def create(self, audit: dict) -> None:
        db = await get_db()
        try:
            await db.execute(
                """INSERT INTO audit_logs
                   (id, operator_id, action, target_type, target_id, success, detail, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    audit["id"], audit["operator_id"], audit["action"],
                    audit["target_type"], audit.get("target_id"),
                    1 if audit.get("success", True) else 0,
                    audit.get("detail"), audit["created_at"],
                ),
            )
            await db.commit()
        except Exception:
            await db.rollback()
            raise
    async def list(
        self, page: int = 1, page_size: int = 20,
        operator_id: Optional[str] = None, operator_username: Optional[str] = None,
        action: Optional[str] = None,
        target_id: Optional[str] = None,
        start_time: Optional[str] = None, end_time: Optional[str] = None,
    ) -> Tuple[List[dict], int]:
        db = await get_db()
        where_parts: List[str] = []
        params: List = []
        if operator_id is not None:
            where_parts.append("a.operator_id = ?"); params.append(operator_id)
        if operator_username is not None:
            where_parts.append("u.username = ?"); params.append(operator_username)
        if action is not None:
            where_parts.append("a.action = ?"); params.append(action)
        if target_id is not None:
            where_parts.append("a.target_id = ?"); params.append(target_id)
        if start_time is not None:
            where_parts.append("a.created_at >= ?"); params.append(start_time)
        if end_time is not None:
            where_parts.append("a.created_at <= ?"); params.append(end_time)
        where_clause = (" WHERE " + " AND ".join(where_parts)) if where_parts else ""
        offset = (page - 1) * page_size
        cursor = await db.execute(
            f"""SELECT a.id, a.operator_id, a.action, a.target_type, a.target_id,
                       a.success, a.detail, a.created_at, u.username AS operator_username
                FROM audit_logs AS a
                LEFT JOIN users AS u ON u.id = a.operator_id
                {where_clause}
                ORDER BY a.created_at DESC, a.id DESC
                LIMIT ? OFFSET ?""",
            params + [page_size, offset],
        )
        rows = await cursor.fetchall()
        items = [
            {
                "id": r["id"], "operator_id": r["operator_id"],
                "operator_username": r["operator_username"] if "operator_username" in r.keys() else None,
                "action": r["action"], "target_type": r["target_type"],
                "target_id": r["target_id"], "success": bool(r["success"]),
                "detail": r["detail"], "created_at": r["created_at"],
            }
            for r in rows
        ]
        cursor = await db.execute(
            f"SELECT COUNT(*) FROM audit_logs AS a LEFT JOIN users AS u ON u.id = a.operator_id{where_clause}",
            params,
        )
        total = (await cursor.fetchone())[0]
        return items, total
audit_log_repository = AuditLogRepository()