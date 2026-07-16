from typing import Optional
from app.models.user import UserRegister
from app.repositories.user_repository import user_repository
from app.utils.id_gen import generate_uuid
from app.utils.errors import ConflictError
from app.utils.password import hash_password,verify_password
from app.utils.time import now_utc
class AuthService:
    async def register(self,data:UserRegister):
        if await user_repository.username_exists(data.username):
            raise ConflictError('username already exists')
        ts=now_utc()
        user={
            'id':generate_uuid(),
            'username':data.username,
            'password_hash':hash_password(data.password),
            'role':'student',
            'is_active':True,
            'created_at':ts,
            'updated_at':ts,
        }
        await user_repository.create(user)
        return self._public_view(user)
    async def authenticate(self,username:str,password:str):
        user=await user_repository.get_by_username(username)
        if user is None:
            verify_password(password,"$2b$12$"+"x"*53)
            return None
        if not verify_password(password,user["password_hash"]):
            return None
        return user
    def save_session(self,user:dict,session):
        session['user_id']=user['id']
    def clear_session(self,session):
        session.clear()#q
    @staticmethod
    def _public_view(user:dict):
        return {
            'id':user['id'],
            'username':user['username'],
            'role':user['role'],
            'is_active':user['is_active'],
            'created_at':user['created_at'],
            'updated_at':user['updated_at'],
        }
auth_service=AuthService()