from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.db import get_session
from modules.transactions.wallet import process_wallet_to_wallet_transfer, generate_virtual_account_number
from database.schema import WalletTransferRequest, GenerateVirtualAccountRequest, GenerateVirtualAccountResponse, ErrorResponse, PlainResponse

router = APIRouter(
    prefix="/wallet",
    tags=["Wallet Transactions"]
)

@router.post("/transfer", response_model=PlainResponse, responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def wallet_to_wallet_transfer(payload: WalletTransferRequest, db: Session = Depends(get_session)):
    """
    Endpoint to transfer funds between two user wallets.
    """
    return process_wallet_to_wallet_transfer(
        db,
        from_user_id=payload.from_user_id,
        to_user_id=payload.to_user_id,
        amount=payload.amount,
        narration=payload.narration
    )
    

@router.post("/generate-virtual-account", response_model=GenerateVirtualAccountResponse, responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def create_virtual_account(payload: GenerateVirtualAccountRequest, db: Session = Depends(get_session)):
    """
    Endpoint to generate a virtual account for a user.
    """
    return generate_virtual_account_number(db, user_id=payload.user_id)
    