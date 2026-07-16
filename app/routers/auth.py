from fastapi import APIRouter, Depends, Request
from app.models.common import created, ok
from app.models.user import UserLogin, UserRegister
from app.services.auth_service import auth_service
from app.utils.auth import get_current_user
from app.utils.errors import ForbiddenError, UnauthorizedError
router = APIRouter(prefix="/api/auth", tags=["auth"])
@router.post("/register", status_code=201)
async def register(body: UserRegister):
    user = await auth_service.register(body)
    return created(data=user, message="user registered")
@router.post("/login")
async def login(body: UserLogin, request: Request):
    user = await auth_service.authenticate(body.username, body.password)
    if user is None:
        raise UnauthorizedError("invalid credentials")
    if not user["is_active"]:
        raise ForbiddenError("user is disabled")
    auth_service.save_session(user, request.session)
    return ok(
        data={
            "id": user["id"],
            "username": user["username"],
            "role": user["role"],
        },
        message="logged in",
    )
@router.post("/logout")
async def logout(request: Request):
    auth_service.clear_session(request.session)
    return ok(message="logged out")
@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    return ok(data=user)
__all__ = ["router"]