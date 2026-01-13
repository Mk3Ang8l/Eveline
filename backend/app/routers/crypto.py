from fastapi import APIRouter, HTTPException
from ..services.crypto_service import CryptoService
from ..schemas.all_schemas import CryptoBalanceRequest, CryptoTransferRequest
from typing import List, Dict

router = APIRouter()

@router.get("/balance/{address}")
def get_balance(address: str):
    """Fetch balance for a given wallet address"""
    res = CryptoService.get_balance(address)
    if "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])
    return res

@router.get("/history/{address}")
def get_history(address: str):
    """Fetch transaction history for a given wallet address"""
    return CryptoService.get_transactions(address)

@router.post("/prepare")
def prepare_tx(req: CryptoTransferRequest):
    """Prepare a transaction to be signed by the user"""
    res = CryptoService.prepare_transfer(req.from_address, req.to_address, req.amount)
    if "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])
    return res
