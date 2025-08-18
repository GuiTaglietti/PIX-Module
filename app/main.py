# app/main.py
from __future__ import annotations
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from app.config import settings
from app.container import initialize_container, container


def create_app() -> FastAPI:
    initialize_container()
    
    app = FastAPI(title=settings.app_name, debug=settings.debug)
    
    @app.get("/", response_class=HTMLResponse)
    def index(request: Request):
        templates = container["templates"]
        return templates.TemplateResponse("index.html", {"request": request})
    
    from app.api.v1.router import router as api_router
    app.include_router(api_router)
    
    return app


app = create_app()
