# app/container.py
from __future__ import annotations
from typing import Dict, Any
from app.store.db import Database
from app.store.repository import Repository
from app.config import settings
from app.services.pix import Pix

container: Dict[str, Any] = {}

def initialize_container() -> None:
    db = Database(settings.database_url)
    repo = Repository(db, auto_create=settings.auto_create)
    psp = Pix(settings)
    
    container["repo"] = repo
    container["psp"] = psp

