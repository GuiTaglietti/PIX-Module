# app/api/v1/router.py
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from app.store.repository import Repository
from app.models.schemas import CreateUserRequest, UserResponse, CreatePaymentRequest, PaymentResponse, WebhookPix, PaymentStatus
#from app.services.pix.efipay import Efipay, PixError
from app.services.pix.modobank import Modobank, PixError
from app.container import container

router = APIRouter(prefix="/api/v1")

def get_repo() -> Repository:
    return container["repo"]

def get_psp() -> Modobank:
#def get_psp() -> Efipay:
    return container["psp"]

@router.post("/users", response_model=UserResponse)
def create_user(req: CreateUserRequest, repo: Repository = Depends(get_repo)) -> UserResponse:
    user = repo.get_or_create_user(req.cpf, req.email, req.name)
    return UserResponse(cpf=user.cpf, email=user.email, name=user.name)

@router.post("/payments/pix", response_model=PaymentResponse)
def create_payment(req: CreatePaymentRequest, repo: Repository = Depends(get_repo), psp: Modobank = Depends(get_psp)) -> PaymentResponse:
#def create_cob(req: CreatePaymentRequest, repo: Repository = Depends(get_repo), psp: Efipay = Depends(get_psp)) -> PaymentResponse:
    if req.amount <= 0:
        raise HTTPException(status_code=422, detail="amount must be positive")
    try:
        amount_str = f"{req.amount:.2f}"

        response = psp.create_immediate(value=amount_str, cpf=req.cpf, name=req.name)
        txid = response.get("txid")
        pixCopiaECola = response.get("pixCopiaECola")
        
        if not txid or not pixCopiaECola:
            raise HTTPException(status_code=500, detail="Invalid response from payment provider")

        user_cpf: Optional[int] = None
        if req.email:
            user = repo.get_or_create_user(req.cpf, req.email, req.name)
            user_cpf = user.cpf

        payment = repo.create_payment(
            txid=txid, 
            user_cpf=user_cpf, 
            amount=int(round(req.amount)), 
            pixCopiaECola=pixCopiaECola,
        )

        return PaymentResponse(
            status=payment.status,
            user_cpf=payment.user_cpf,
            txid=payment.txid,
            amount=payment.amount,
            pixCopiaECola=payment.pixCopiaECola,
            )
        
    except PixError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create payment: {str(e)}")

@router.get("/payments/pix/{txid}", response_model=PaymentResponse)
def get_payment(txid: str, repo: Repository = Depends(get_repo)) -> PaymentResponse:
    payment = repo.get_payment(txid)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    return PaymentResponse(
        txid=payment.txid,
        user_cpf=payment.user_cpf,
        amount=payment.amount,
        status=payment.status,
        pixCopiaECola=payment.pixCopiaECola,
    )

# NOTE: this was not tested after refactor
@router.post("/payments/pix/{txid}/check", response_model=PaymentResponse)
#def check_payment_status(txid: str, repo: Repository = Depends(get_repo), psp: Efipay = Depends(get_psp)) -> PaymentResponse:
def check_payment_status(txid: str, repo: Repository = Depends(get_repo), psp: Modobank = Depends(get_psp)) -> PaymentResponse:
    try:
        payment = repo.get_payment(txid)
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        response = psp.detail_immediate(txid)
        status = response.get("status", "").upper()
        
        if status in ["CONCLUIDA"]:
            new_status = PaymentStatus.CONCLUDED
        elif status in ["ATIVA"]:
            new_status = PaymentStatus.ACTIVE
        elif status in ["REMOVIDA_PELO_USUARIO_RECEBEDOR"]:
            new_status = PaymentStatus.REMOVED_BY_USER
        elif status in ["REMOVIDA_PELO_PSP"]:
            new_status = PaymentStatus.REMOVED_BY_PSP
        else:
            new_status = PaymentStatus.ACTIVE
        
        if payment.status != new_status:
            payment = repo.set_status(txid, new_status)
        
        return PaymentResponse(
            txid=payment.txid,
            status=payment.status,
            user_cpf=payment.user_cpf,
            amount=payment.amount,
            pixCopiaECola=payment.pixCopiaECola,
        )
        
    except PixError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to check payment status")

# NOTE: this was not tested after refactor
@router.get("/payments/pix")
#def list_payments(inicio: str, fim: str, psp: Efipay = Depends(get_psp)) -> dict:
def list_payments(inicio: str, fim: str, psp: Modobank = Depends(get_psp)) -> dict:
    try:
        return psp.list_immediate(inicio, fim)
    except PixError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to list payments")

# NOTE: i dont even know if it works
@router.post("/webhooks/pix")
def immediate_webhook(webhook: WebhookPix, repo: Repository = Depends(get_repo)):
    try:
        payment = repo.set_status(webhook.txid, webhook.status)
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        return {
            "status": "ok",
            "message": "Payment updated successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to process webhook")
