from typing import Optional
from fastapi import Depends, Request
from app.repositories.user_repository import user_repository
from app.utils.errors import ForbiddenError, UnauthorizedError
async def get_current_user(request: Request) -> dict:
    user_id = request.session.get("user_id")
    if not user_id:
       raise UnauthorizedError()
    user = await user_repository.get_by_id(user_id)
    if user is None:
        request.session.clear()
        raise UnauthorizedError()
    if not user["is_active"]:
        raise ForbiddenError("user is disabled")
    return _strip_password_hash(user)
async def require_active(user: dict = Depends(get_current_user)) -> dict:
    return user
async def require_teacher_or_admin(user: dict = Depends(get_current_user)) -> dict:
    if user["role"] not in ("teacher", "admin"):
        raise ForbiddenError("teacher or admin role required")
    return user
async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user["role"] != "admin":
        raise ForbiddenError("admin role required")
    return user
def _strip_password_hash(user: dict) -> dict:
    return {
        "id": user["id"],
        "username": user["username"],
        "role": user["role"],
        "is_active": user["is_active"],
        "created_at": user["created_at"],
        "updated_at": user["updated_at"],
    }