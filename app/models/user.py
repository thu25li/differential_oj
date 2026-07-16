from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
class Role(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"
class UserRegister(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=8, max_length=128)
class UserLogin(BaseModel):
    username: str = Field(min_length=1, max_length=32)
    password: str = Field(min_length=1, max_length=128)
class UserUpdate(BaseModel):
    role: Optional[Role] = None
    is_active: Optional[bool] = None
class UserResponse(BaseModel):
    id: str
    username: str
    role: Role
    is_active: bool
    created_at: str
    updated_at: str