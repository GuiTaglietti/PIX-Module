# app/models/schemas.py
from __future__ import annotations
from pydantic import BaseModel, Field, EmailStr
from pydantic_br import CPF
from enum import Enum
from typing import Optional, Dict, Any

class PaymentStatus(str, Enum):
    ACTIVE = "ATIVA"
    CONCLUDED = "CONCLUIDA"
    REMOVED_BY_USER = "REMOVIDA_PELO_USUARIO_RECEBEDOR"
    REMOVED_BY_PSP = "REMOVIDA_PELO_PSP"

class CreateUserRequest(BaseModel): # TODO: ask Paulinho which data we wish to collect
    # password
    # agency: Optional[str] = None
    # account: Optional[str] = None
    # ispb: Optional[str] = None
    cpf: CPF
    email: EmailStr
    name: str

class UserResponse(BaseModel):
    # password ?
    # agency: Optional[str] = None
    # account: Optional[str] = None
    # ispb: Optional[str] = None
    cpf: CPF
    email: EmailStr
    name: str

class CreatePaymentRequest(BaseModel): # TODO: see which data we want to send in the payment request
    # created at
    amount: float = Field(..., gt=0, description="Amount in BRL")
    cpf: CPF
    name: str
    email: str
    # aditional info

class PaymentResponse(BaseModel): # TODO: RFC-3339 to unix epoch or another postgresql supported fmt
    # created_at:
    txid: str
    status: PaymentStatus
    user_cpf: CPF
    amount: float = Field(..., gt=0, description="Amount in BRL")
    pixCopiaECola: str
    # aditional info

class WebhookPix(BaseModel):
    txid: str
    status: PaymentStatus

class WebhookRequest(BaseModel):
    webhook_url: str
    
class WebhookResponse(BaseModel):
    webhook_url: str
    status: str
    message: str
    psp_response: Optional[Dict[Any, Any]] = None
