from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field
T = TypeVar("T")
class ApiResponse(BaseModel, Generic[T]):
    code: int = 200
    message: str = "ok"
    data: Optional[T] = None
class PageParams(BaseModel):
    page: int = Field(default=1, ge=1, description="页码，从 1 开始")
    page_size: int = Field(default=20, ge=1, le=100, description="每页大小，1-100")
class PageData(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
def ok(data: Any = None, message: str = "ok") -> dict:
    return {"code": 200, "message": message, "data": data}
def created(data: Any = None, message: str = "created") -> dict:
    return {"code": 201, "message": message, "data": data}
def accepted(data: Any = None, message: str = "accepted") -> dict:
    return {"code": 202, "message": message, "data": data}