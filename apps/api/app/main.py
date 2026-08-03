from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import PlainTextResponse

from app.config import settings
from app.db import init_db
from app.routes import router
from app.routes_account import router as account_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    yield


class LocalCorsMiddleware(BaseHTTPMiddleware):
    """Always allow browser calls from Next.js (localhost / 127.0.0.1 / any port)."""

    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin") or "*"
        allow_origin = "*" if origin == "null" else origin

        if request.method == "OPTIONS":
            req_headers = request.headers.get("access-control-request-headers") or "*"
            return PlainTextResponse(
                "ok",
                status_code=200,
                headers={
                    "Access-Control-Allow-Origin": allow_origin,
                    "Access-Control-Allow-Methods": "DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT",
                    "Access-Control-Allow-Headers": req_headers,
                    "Access-Control-Max-Age": "600",
                    "Vary": "Origin",
                },
            )

        response: Response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = allow_origin
        response.headers["Vary"] = "Origin"
        return response


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(LocalCorsMiddleware)
app.include_router(router, prefix="/api")
app.include_router(account_router, prefix="/api")

app.mount("/uploads", StaticFiles(directory=str(settings.uploads_dir)), name="uploads")
app.mount("/generated", StaticFiles(directory=str(settings.generated_dir)), name="generated")
app.mount("/previews", StaticFiles(directory=str(settings.previews_dir), html=True), name="previews")


@app.get("/")
async def root():
    return {
        "name": "AdzMate Campaign Auto-Pilot",
        "docs": "/docs",
        "health": "/api/health",
    }
