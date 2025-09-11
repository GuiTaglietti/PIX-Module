# app/api/v1/router.py
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Optional
from app.store.repository import Repository
from app.models.schemas import (
    CreateUserRequest, UserResponse, CreatePaymentRequest, PaymentResponse, 
    PaymentStatus, WebhookPix, WebhookRequest, WebhookResponse, PaymentStatusUpdate
)
from app.services.pix import Pix, PixError, WebhookError
from app.container import container
from app.auth import get_api_key

router = APIRouter(prefix="/api/v1")

def get_repo() -> Repository:
    return container["repo"]

def get_psp() -> Pix:
    return container["psp"]

@router.post("/users", response_model=UserResponse)
def create_user(
    req: CreateUserRequest, 
    repo: Repository = Depends(get_repo),
    api_key: str = Depends(get_api_key)
) -> UserResponse:
    """
    Create new user. # TODO: documentation
    """
    user = repo.get_or_create_user(req.cpf, req.email, req.name)
    return UserResponse(cpf=user.cpf, email=user.email, name=user.name)

@router.post("/pix", response_model=PaymentResponse)
def create_immediate_charge(
    req: CreatePaymentRequest, 
    repo: Repository = Depends(get_repo), 
    psp: Pix = Depends(get_psp),
    api_key: str = Depends(get_api_key)
) -> PaymentResponse:
    """
    Create an immediate PIX charge. # TODO: documentation
    """
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

@router.get("/pix/{txid}", response_model=PaymentResponse)
def detail_payment(
    txid: str, 
    repo: Repository = Depends(get_repo), 
    psp: Pix = Depends(get_psp),
    api_key: str = Depends(get_api_key)
) -> PaymentResponse:
    """
    Get detailed information about a specific payment. #TODO: documentation
    """
    try:
        payment = repo.get_payment(txid)
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        psp_response = psp.detail_immediate_charge(txid)
        psp_status = psp_response.get("status", "").upper()
        
        return PaymentResponse(
            txid=payment.txid,
            status=payment.status,
            user_cpf=payment.user_cpf,
            amount=payment.amount,
            pixCopiaECola=payment.pixCopiaECola,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get payment details")

@router.put("/pix/{txid}/status", response_model=PaymentResponse)
def update_payment_status(
    txid: str, 
    repo: Repository = Depends(get_repo), 
    psp: Pix = Depends(get_psp),
    api_key: str = Depends(get_api_key)  # Require API key
) -> PaymentResponse:
    """
    Update payment status by fetching latest status from PSP. # TODO: documentation
    """
    try:
        payment = repo.get_payment(txid)
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        response = psp.detail_immediate_charge(txid)
        psp_status = response.get("status", "").upper()
        
        if psp_status in ["CONCLUIDA"]:
            new_status = PaymentStatus.CONCLUDED
        elif psp_status in ["ATIVA"]:
            new_status = PaymentStatus.ACTIVE
        elif psp_status in ["REMOVIDA_PELO_USUARIO_RECEBEDOR"]:
            new_status = PaymentStatus.REMOVED_BY_USER
        elif psp_status in ["REMOVIDA_PELO_PSP"]:
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
        logger.error(f"PIX error updating payment status for {txid}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to check payment status")

@router.get("/pix")
def list_immediate_charges(
    inicio: str, 
    fim: str, 
    psp: Pix = Depends(get_psp),
    api_key: str = Depends(get_api_key)
) -> dict:
    """
    List immediate charges between dates. # TODO: documentation
    """
    try:
        result = psp.list_immediate_charges(inicio, fim)
        return result
    except PixError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to list payments")

@router.post("/webhooks/config", response_model=WebhookResponse)
def create_webhook(
    req: WebhookRequest, 
    psp: Pix = Depends(get_psp),
    api_key: str = Depends(get_api_key)
) -> WebhookResponse:
    """
    Register a webhook URL with the PSP. Requires API key authentication. # TODO: documentation
    """
    try:
        webhook_url_str = str(req.webhook_url)
        response = psp.create_webhook(webhook_url_str)
        
        return WebhookResponse(
            webhook_url=webhook_url_str,
            status="registered",
            message="Webhook registered successfully",
            psp_response=response
        )
        
    except WebhookError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to register webhook: {str(e)}")

@router.get("/webhooks/config", response_model=WebhookResponse)
def get_webhook_config(
    psp: Pix = Depends(get_psp),
    api_key: str = Depends(get_api_key)
) -> WebhookResponse:
    """
    Get current webhook configuration. Requires API key authentication. # TODO: documentation
    """
    try:
        response = psp.get_webhook()
        webhook_url = response.get("webhookUrl", "")
        
        return WebhookResponse(
            webhook_url=webhook_url,
            status="active" if webhook_url else "not_configured",
            message="Current webhook configuration",
            psp_response=response
        )
        
    except WebhookError as e:
        return WebhookResponse(
            webhook_url="",
            status="not_configured",
            message="No webhook configured",
            psp_response={}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get webhook config: {str(e)}")

@router.delete("/webhooks/config")
def delete_webhook(
    psp: Pix = Depends(get_psp),
    api_key: str = Depends(get_api_key)
) -> dict:
    """
    Delete webhook configuration. Requires API key authentication. # TODO: documentation
    """
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
def receive_pix_webhook(
    webhook: WebhookPix, 
    request: Request, 
    repo: Repository = Depends(get_repo)
):
    """
    Receive webhook notifications from PSP when payments are made. # TODO: documentation
    """
    try:
        client_ip = request.client.host if request.client else "unknown"
        
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

