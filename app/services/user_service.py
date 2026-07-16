from app.models.user import UserUpdate
from app.repositories.user_repository import user_repository
from app.utils.errors import BadRequestError, NotFoundError
from app.utils.time import now_utc
class UserService:
    async def list_users(self, page: int = 1, page_size: int = 20) -> dict:
        items, total = await user_repository.list(page=page, page_size=page_size)
        return {"items": items, "total": total, "page": page, "page_size": page_size}
    async def get_user(self, user_id: str) -> dict:
        user = await user_repository.get_by_id(user_id)
        if user is None:
            raise NotFoundError("user not found")
        return self._public_view(user)
    async def update_user(
        self,
        user_id: str,
        updates: UserUpdate,
        current_user: dict,
    ) -> dict:
        if not await user_repository.exists(user_id):
            raise NotFoundError("user not found")
        if (
            user_id == current_user["id"]
            and updates.is_active is False
        ):
            raise BadRequestError("cannot disable yourself")
        update_dict = {
            "role": updates.role.value if updates.role is not None else None,
            "is_active": updates.is_active,
            "updated_at": now_utc(),
        }
        ok = await user_repository.update(user_id, update_dict)
        if not ok:
            raise NotFoundError("user not found")
        updated = await user_repository.get_by_id(user_id)
        return self._public_view(updated)
    @staticmethod
    def _public_view(user: dict) -> dict:
        return {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"],
            "is_active": user["is_active"],
            "created_at": user["created_at"],
            "updated_at": user["updated_at"],
        }
user_service = UserService()