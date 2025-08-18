# app/container.py
from __future__ import annotations
from typing import Dict, Any
from app.store.db import Database
from app.store.repository import Repository
from app.config import settings
from app.services.pix.modobank import Modobank
#from app.services.pix.efipay import Efipay
from fastapi.templating import Jinja2Templates
import pathlib

container: Dict[str, Any] = {}

def initialize_container() -> None:
    db = Database(settings.database_url)
    repo = Repository(db, auto_create=settings.auto_create)
    psp = Modobank(settings)
    templates = Jinja2Templates(directory=str(pathlib.Path(__file__).parent / "web" / "templates"))
    
    container["repo"] = repo
    container["psp"] = psp
    container["templates"] = templates

