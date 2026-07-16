import json
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from app import database as db_module
from app.database import close_database, get_db, init_database
from app.repositories.audit_log_repository import audit_log_repository
from app.repositories.backup_repository import backup_repository
from app.utils.errors import BadRequestError, NotFoundError, SystemError
from app.utils.id_gen import generate_uuid
from app.utils.time import now_utc
def _backups_dir() -> Path:
    bd = db_module.DB_PATH.parent / "backups"
    bd.mkdir(parents=True, exist_ok=True)
    return bd
class BackupService:
    async def create_backup(self, current_user: dict) -> dict:
        backup_id = f"backup_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')}"
        backup_dir = _backups_dir() / backup_id
        backup_dir.mkdir(parents=True, exist_ok=True)
        db_file = backup_dir / "oj.db"
        manifest_file = backup_dir / "manifest.json"
        db = await get_db()
        await db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        await db.commit()
        src = sqlite3.connect(str(db_module.DB_PATH))
        dst = sqlite3.connect(str(db_file))
        try:
            src.backup(dst)
        finally:
            dst.close()
            src.close()
        ts = now_utc()
        size = db_file.stat().st_size
        manifest = {
            "backup_id": backup_id,
            "created_at": ts,
            "storage_type": "sqlite",
            "files": ["oj.db"],
            "total_size_bytes": size,
        }
        manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        await backup_repository.create({
            "backup_id": backup_id,
            "created_at": ts,
            "storage_type": "sqlite",
            "file_count": 1,
            "total_size_bytes": size,
            "manifest_path": str(manifest_file),
        })
        await audit_log_repository.create({
            "id": generate_uuid(),
            "operator_id": current_user["id"],
            "action": "CREATE_BACKUP",
            "target_type": "backup",
            "target_id": backup_id,
            "success": True,
            "detail": None,
            "created_at": ts,
        })
        return {"backup_id": backup_id, "created_at": ts}
    async def list_backups(self) -> dict:
        items, total = await backup_repository.list()
        return {"items": items, "total": total}
    async def restore_backup(self, backup_id: str, current_user: dict) -> dict:
        record = await backup_repository.get(backup_id)
        if record is None:
            raise NotFoundError("backup not found")
        backup_dir = _backups_dir() / backup_id
        manifest_file = backup_dir / "manifest.json"
        db_backup = backup_dir / "oj.db"
        try:
            manifest_text = manifest_file.read_text(encoding="utf-8")
            manifest = json.loads(manifest_text)
        except FileNotFoundError:
            raise BadRequestError("manifest.json missing")
        except json.JSONDecodeError:
            raise BadRequestError("manifest.json is not valid JSON")
        for key in ("backup_id", "created_at", "storage_type", "files"):
            if key not in manifest:
                raise BadRequestError(f"manifest missing field: {key}")
        if not db_backup.exists():
            raise BadRequestError("backup database file missing")
        safety_path = db_module.DB_PATH.with_suffix(".db.safety")
        try:
            shutil.copy2(str(db_module.DB_PATH), str(safety_path))
        except Exception as e:
            raise SystemError(f"failed to create safety copy: {e}")
        ts = now_utc()
        success = True
        detail = None
        try:
            await close_database()
            shutil.copy2(str(db_backup), str(db_module.DB_PATH))
            for suffix in ("-wal", "-shm"):
                p = db_module.DB_PATH.with_name(db_module.DB_PATH.name + suffix)
                if p.exists():
                    p.unlink()
            await init_database()
        except Exception as e:
            success = False
            detail = f"restore failed: {e}"
            try:
                if db_module.DB_PATH.exists():
                    db_module.DB_PATH.unlink()
                shutil.copy2(str(safety_path), str(db_module.DB_PATH))
                await init_database()
            except Exception:
                detail += "; rollback also failed"
            raise SystemError(f"restore failed, rolled back: {e}")
        finally:
            if safety_path.exists():
                safety_path.unlink()
        await audit_log_repository.create({
            "id": generate_uuid(),
            "operator_id": current_user["id"],
            "action": "RESTORE_BACKUP",
            "target_type": "backup",
            "target_id": backup_id,
            "success": success,
            "detail": detail,
            "created_at": ts,
        })
        return {"backup_id": backup_id, "restored_at": ts}
backup_service = BackupService()
