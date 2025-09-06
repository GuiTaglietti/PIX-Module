# app/config.py
from __future__ import annotations
import os
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Optional

load_dotenv()

@dataclass
class Settings: # NOTE: is it safe to leave the keys in this class??
    app_name: str = "PIX-Module"
    debug: bool = os.getenv("DEBUG", "0") == "1"
    database_url: Optional[str] = os.getenv("DATABASE_URL")
    psp_client_id: Optional[str] = os.getenv("MODOBANK_CLIENT_ID")
    psp_client_secret: Optional[str] = os.getenv("MODOBANK_CLIENT_SECRET")
    psp_pfx_path: Optional[str] = os.getenv("MODOBANK_PFX_PATH")
    psp_crt_path: Optional[str] = os.getenv("MODOBANK_CRT_PATH")
    psp_key_path: Optional[str] = os.getenv("MODOBANK_KEY_PATH")
    psp_pix_key: Optional[str] = os.getenv("RECEIVER_PIX_KEY")
    auto_create: bool = True

    def __post_init__(self):
        required_vars = [
            ("DATABASE_URL", self.database_url),
            ("MODOBANK_CLIENT_ID", self.psp_client_id),
            ("MODOBANK_CLIENT_SECRET", self.psp_client_secret),
            ("RECEIVER_PIX_KEY", self.psp_pix_key),
        ]
        cert_vars = [
            ("MODOBANK_CRT_PATH", self.psp_crt_path),
            ("MODOBANK_KEY_PATH", self.psp_key_path),
        ]
        
        missing_vars = [var_name for var_name, value in required_vars if not value]
        missing_certs = [var_name for var_name, value in cert_vars if not value]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        if missing_certs and self.debug:
            print(f"Warning: Missing certificate paths: {', '.join(missing_certs)}")
        elif missing_certs and not self.debug:
            raise ValueError(f"Missing required certificate paths: {', '.join(missing_certs)}")

settings = Settings()
