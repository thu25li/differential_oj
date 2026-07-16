import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware
from app.database import close_database, init_database
from app.routers import auth as auth_router
from app.routers import problems as problems_router
from app.utils.errors import OJError
from app.routers import users as users_router
from app.routers import submissions as submissions_router
from app.routers import logs as logs_router
from app.routers import admin as admin_router
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_database()
    try:
        yield
    finally:
        await close_database()
app = FastAPI(title="OJ System", lifespan=lifespan)
SECRET_KEY = os.environ.get("OJ_SECRET_KEY",
"dev-secret-key-change-in-production-please")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
app.include_router(auth_router.router)
app.include_router(problems_router.router)
app.include_router(users_router.router)
app.include_router(submissions_router.router)
app.include_router(logs_router.router)
app.include_router(admin_router.router)
@app.exception_handler(OJError)
async def oj_error_handler(request: Request, exc: OJError):
    return JSONResponse(
        status_code=exc.code,
        content={"code": exc.code, "message": exc.message, "data": exc.data},
    )
@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    logger.warning(
        "validation failed on %s %s: %s",
        request.method,
        request.url.path,
        exc.errors(),
    )
    return JSONResponse(
        status_code=422,
        content={
            "code": 422,
            "message": "request validation failed",
            "data": None,
        },
    )
@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    logger.exception(
        "unhandled exception on %s %s",
        request.method,
        request.url.path,
    )
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": "internal server error",
            "data": None,
        },
    )
@app.get("/")
async def root():
    return {"code": 200, "message": "ok", "data": {"service": "oj"}}