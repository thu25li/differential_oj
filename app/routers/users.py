from fastapi import APIRouter, Depends, Query
from app.models.common import ok
from app.models.user import UserUpdate
from app.services.user_service import user_service
from app.utils.auth import require_admin
router = APIRouter(prefix="/api/users", tags=["users"])
@router.get("")
async def list_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current: dict = Depends(require_admin),
):
    data = await user_service.list_users(page=page, page_size=page_size)
    return ok(data=data)
@router.get("/{user_id}")
async def get_user(
    user_id: str,
    current: dict = Depends(require_admin),
):
    data = await user_service.get_user(user_id)
    return ok(data=data)
@router.put("/{user_id}")
async def update_user(
    user_id: str,
    body: UserUpdate,
    current: dict = Depends(require_admin),
):
    data = await user_service.update_user(user_id, body, current)
    return ok(data=data, message="user updated")
__all__ = ["router"]