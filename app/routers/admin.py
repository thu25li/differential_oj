from fastapi import APIRouter, Depends
from app.models.common import created, ok
from app.services.backup_service import backup_service
from app.utils.auth import require_admin
router = APIRouter(prefix="/api/admin", tags=["admin"])
@router.post("/backups", status_code=201)
async def create_backup(user: dict = Depends(require_admin)):
    data = await backup_service.create_backup(user)
    return created(data=data, message="backup created")
@router.get("/backups")
async def list_backups(user: dict = Depends(require_admin)):
    data = await backup_service.list_backups()
    return ok(data=data)
@router.post("/backups/{backup_id}/restore")
async def restore_backup(
    backup_id: str,
    user: dict = Depends(require_admin),
):
    data = await backup_service.restore_backup(backup_id, user)
    return ok(data=data, message="backup restored")
__all__ = ["router"]
