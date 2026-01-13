from fastapi import APIRouter, HTTPException
from ..services.account_service import AccountService

router = APIRouter()

@router.get("/accounts")
async def get_accounts():
    """Returns a list of all domains with saved browser sessions."""
    try:
        return AccountService.list_accounts()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/accounts/{domain}")
async def delete_account(domain: str):
    """Deletes a saved session for a specific domain."""
    success = AccountService.delete_session(domain)
    if not success:
        raise HTTPException(status_code=404, detail=f"No session found for {domain}")
    return {"message": f"Session for {domain} deleted"}
