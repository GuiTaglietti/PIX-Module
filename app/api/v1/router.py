# app/api/v1/router.py
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Optional
from app.store.repository import Repository
from app.models.schemas import CreateUserRequest, UserResponse, CreatePaymentRequest, PaymentResponse, PaymentStatus, WebhookPix, WebhookRequest, WebhookResponse
from app.services.pix import Pix, PixError, WebhookError
from app.container import container

router = APIRouter(prefix="/api/v1")

def get_repo() -> Repository:
    return container["repo"]

def get_psp() -> Pix:
    return container["psp"]

@router.post("/users", response_model=UserResponse)
def create_user(req: CreateUserRequest, repo: Repository = Depends(get_repo)) -> UserResponse: # TODO: remove user creation
    user = repo.get_or_create_user(req.cpf, req.email, req.name)
    return UserResponse(cpf=user.cpf, email=user.email, name=user.name)

@router.post("/pix", response_model=PaymentResponse)
def create_immediate_charge(req: CreatePaymentRequest, repo: Repository = Depends(get_repo), psp: Pix = Depends(get_psp)) -> PaymentResponse:
    if req.amount <= 0:
        raise HTTPException(status_code=422, detail="amount must be positive")
    try:
        amount_str = f"{req.amount:.2f}"

        response = psp.create_immediate_charge(amount=amount_str, cpf=req.cpf, name=req.name)
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
            amount=int(round(req.amount * 100)),
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

@router.post("/pix/{txid}", response_model=PaymentResponse)
def update_payment_status(txid: str, repo: Repository = Depends(get_repo), psp: Pix = Depends(get_psp)) -> PaymentResponse:
    try:
        payment = repo.get_payment(txid)
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        response = psp.detail_immediate_charge(txid)
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

@router.get("/pix")
def list_immediate_charges(inicio: str, fim: str, psp: Pix = Depends(get_psp)) -> dict:
    try:
        return psp.list_immediate_charges(inicio, fim)
    except PixError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to list payments")

@router.post("/webhooks/config", response_model=WebhookResponse)
def create_webhook(req: WebhookRequest, psp: Pix = Depends(get_psp)) -> WebhookResponse:
    try:
        response = psp.create_webhook(req.webhook_url)
        
        return WebhookResponse(
            webhook_url=req.webhook_url,
            status="registered",
            message="Webhook registered successfully",
            psp_response=response
        )
        
    except WebhookError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to register webhook: {str(e)}")

@router.delete("/webhooks/config")
def delete_webhook(psp: Pix = Depends(get_psp)) -> dict:
    try:
        response = psp.delete_webhook()
        
        return {
            "status": "deleted",
            "message": "Webhook deleted successfully",
            "psp_response": response
        }
        
    except WebhookError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete webhook: {str(e)}")

@router.post("/webhooks/pix")
def receive_pix_webhook(webhook: WebhookPix, request: Request, repo: Repository = Depends(get_repo)):
    try:
        payment = repo.set_status(webhook.txid, webhook.status)
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        return {
            "status": "ok",
            "message": "Payment updated successfully",
            "txid": webhook.txid,
            "new_status": webhook.status.value
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to process webhook")
