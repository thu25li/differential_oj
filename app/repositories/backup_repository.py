from typing import List, Optional, Tuple
from app.database import get_db
class BackupRepository:
    async def create(self, record: dict) -> None:
        db = await get_db()
        try:
            await db.execute(
                """INSERT INTO backup_records
                   (backup_id, created_at, storage_type, file_count,
                    total_size_bytes, manifest_path)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    record["backup_id"], record["created_at"],
                    record["storage_type"], record["file_count"],
                    record["total_size_bytes"], record["manifest_path"],
                ),
            )
            await db.commit()
        except Exception:
            await db.rollback()
            raise
    async def get(self, backup_id: str) -> Optional[dict]:
        db = await get_db()
        cursor = await db.execute(
            """SELECT backup_id, created_at, storage_type, file_count,
                      total_size_bytes, manifest_path
               FROM backup_records WHERE backup_id = ?""",
            (backup_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return self._row_to_dict(row)
    async def list(self) -> Tuple[List[dict], int]:
        db = await get_db()
        cursor = await db.execute(
            """SELECT backup_id, created_at, storage_type, file_count,
                      total_size_bytes, manifest_path
               FROM backup_records ORDER BY created_at DESC, backup_id DESC"""
        )
        rows = await cursor.fetchall()
        items = [self._row_to_dict(r) for r in rows]
        return items, len(items)
    async def exists(self, backup_id: str) -> bool:
        db = await get_db()
        cursor = await db.execute(
            "SELECT 1 FROM backup_records WHERE backup_id = ?",
            (backup_id,),
        )
        return await cursor.fetchone() is not None
    @staticmethod
    def _row_to_dict(row) -> dict:
        return {
            "backup_id": row["backup_id"],
            "created_at": row["created_at"],
            "storage_type": row["storage_type"],
            "file_count": row["file_count"],
            "total_size_bytes": row["total_size_bytes"],
            "manifest_path": row["manifest_path"],
        }
backup_repository = BackupRepository()
