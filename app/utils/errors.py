from typing import Any, Optional
class OJError(Exception):
    def __init__(self, code: int, message: str, data: Optional[Any] = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)
class BadRequestError(OJError):
    def __init__(self, message: str = "bad request", data: Optional[Any] = None):
        super().__init__(400, message, data)
class UnauthorizedError(OJError):
    def __init__(self, message: str = "not logged in", data: Optional[Any] = None):
        super().__init__(401, message, data)
class ForbiddenError(OJError):
    def __init__(self, message: str = "permission denied", data: Optional[Any] = None):
        super().__init__(403, message, data)
class NotFoundError(OJError):
    def __init__(self, message: str = "resource not found", data: Optional[Any] = None):
        super().__init__(404, message, data)
class ConflictError(OJError):
    def __init__(self, message: str = "resource conflict", data: Optional[Any] = None):
        super().__init__(409, message, data)
class ValidationError(OJError):
    def __init__(self, message: str = "validation failed", data: Optional[Any] = None):
        super().__init__(422, message, data)
class SystemError(OJError):
    def __init__(self, message: str = "internal server error", data: Optional[Any] = None):
        super().__init__(500, message, data)