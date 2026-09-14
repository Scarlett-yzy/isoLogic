# -*- coding: utf-8 -*-
"""FastAPI application for Logic-Coloc."""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .routes import router
from .user_paths import UPLOAD_DIR
from .note_store import ensure_storage
from .service import ServiceError


class CachedStaticFiles(StaticFiles):
    """Cache immutable visual assets so pet animation never re-fetches every frame."""

    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        normalized_path = path.replace("\\", "/")
        if normalized_path.startswith("assets/"):
            # 一天即可：单次会话内素材不会重复下载，而桌宠素材还在反复裁切，
            # 设成一年 immutable 会让老访客永远看不到新图，排查时极易误判。
            response.headers["Cache-Control"] = "public, max-age=86400, immutable"
        else:
            response.headers["Cache-Control"] = "no-cache"
        return response


app = FastAPI(title="Logic-Coloc API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5500", "http://127.0.0.1:5500", "http://localhost:8080", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)


@app.exception_handler(ServiceError)
async def service_error_handler(_request: Request, exc: ServiceError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error": {"code": exc.code, "message": exc.message}})

WEB_DIR = Path(__file__).resolve().parents[1] / "web"
app.mount("/static", CachedStaticFiles(directory=WEB_DIR), name="static")
ensure_storage()
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")
