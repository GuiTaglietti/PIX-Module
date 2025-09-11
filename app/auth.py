# app/auth.py
import os
from typing import Optional
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

load_dotenv()

security = HTTPBearer()

def get_api_key_from_env() -> str:
    """
    Get API key from .env
    """
    api_key = os.getenv("API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key not configured in environment variables"
        )
    return api_key

def get_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Validate API key from Authorization header.
    Expected format: Authorization: Bearer <api_key>
    """
    expected_api_key = get_api_key_from_env()
    
    if credentials.credentials != expected_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return credentials.credentials
