# app/config_efipay.py
from __future__ import annotations
import os
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Optional

load_dotenv() # TODO: i think is better to load it without using a library

@dataclass
class Settings: # TODO: is it safe to leave the keys in this class??
    app_name: str = "Vaquinha"
    debug: bool = os.getenv("DEBUG", "0") == "1"
    database_url: Optional[str] = os.getenv("DATABASE_URL")
    env: str = "EFI_SANDBOX" if debug else "EFI_PROD"
    psp_client_id: Optional[str] = os.getenv(f"{env}_CLIENT_ID")
    psp_client_secret: Optional[str] = os.getenv(f"{env}_CLIENT_SECRET")
    psp_pem_path: Optional[str] = os.getenv(f"{env}_CERTIFICATE_PATH")
    psp_pix_key: Optional[str] = os.getenv(f"{env}_PIX_KEY")
    auto_create: bool = True

    def __post_init__(self):
        required_vars = [
            ("DATABASE_URL", self.database_url),
            (f"{self.env}_CLIENT_ID", self.psp_client_id),
            (f"{self.env}_CLIENT_SECRET", self.psp_client_secret),
            (f"{self.env}_PIX_KEY", self.psp_pix_key)
        ]
        cert_vars = [
            (f"{self.env}_CERTIFICATE_PATH", self.psp_pem_path),
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
