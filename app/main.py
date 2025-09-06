# app/main.py
from __future__ import annotations
from fastapi import FastAPI
from app.config import settings
from app.container import initialize_container


def create_app() -> FastAPI:
    initialize_container()
    
    app = FastAPI(title=settings.app_name,debug=settings.debug,docs_url="/")
     
    from app.api.v1.router import router as api_router
    app.include_router(api_router)
    
    return app


app = create_app()
