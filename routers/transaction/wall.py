from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.db import get_session
from modules.transactions.wallet import process_wallet_to_wallet_transfer, generate_virtual_account_number, transfer_funds_to_project_wallet, transfer_funds_from_project_wallet, process_bulk_wallet_to_wallet_transfer, process_bulk_project_wallet_to_wallet_transfer
from database.schema import WalletTransferRequest, GenerateVirtualAccountRequest, GenerateVirtualAccountResponse, ErrorResponse, PlainResponse, ProjectWalletTransferRequest, BulkWalletTransferRequest, BulkProjectWalletTransferRequest
from modules.authentication.auth import auth

router = APIRouter(
    prefix="/wallet",
    tags=["Wallet Transactions"]
)

@router.post("/transfer", response_model=PlainResponse, responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def wallet_to_wallet_transfer(payload: WalletTransferRequest, user=Depends(auth.auth_wrapper), db: Session = Depends(get_session)):
    """
    Endpoint to transfer funds between two user wallets.
    """
    result = process_wallet_to_wallet_transfer(
        db,
        from_user_id=payload.from_user_id,
        to_user_id=payload.to_user_id,
        amount=payload.amount,
        narration=payload.narration
    )
    if not result.get('status'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get('message')
        )
    return result

@router.post("/bulk-transfer", response_model=PlainResponse, responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def bulk_wallet_to_wallet_transfer(payload: BulkWalletTransferRequest, user=Depends(auth.auth_wrapper), db: Session = Depends(get_session)):
    """
    Endpoint to perform multiple wallet-to-wallet transfers from a single sender to multiple recipients.
    This operation is atomic: if any individual transfer fails, the entire bulk operation is rolled back.
    """
    transfers_data = [t.model_dump() for t in payload.transfers]
    result = process_bulk_wallet_to_wallet_transfer(
        db,
        from_user_id=payload.from_user_id,
        transfers=transfers_data
    )
    if not result.get('status'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get('message')
        )
    
    return result
    

@router.post("/project-bulk-transfer", response_model=PlainResponse, responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def bulk_project_wallet_to_wallet_transfer(payload: BulkProjectWalletTransferRequest, user=Depends(auth.auth_wrapper), db: Session = Depends(get_session)):
    """
    Endpoint to perform multiple wallet-to-wallet transfers from a single sender to multiple recipients.
    This operation is atomic: if any individual transfer fails, the entire bulk operation is rolled back.
    """
    transfers_data = [t.model_dump() for t in payload.transfers]
    result = process_bulk_project_wallet_to_wallet_transfer(
        db,
        project_id=payload.project_id,
        transfers=transfers_data
    )
    if not result.get('status'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get('message')
        )
    
    return result
    

@router.post("/generate-virtual-account")
async def create_virtual_account(payload: GenerateVirtualAccountRequest, user=Depends(auth.auth_wrapper), db: Session = Depends(get_session)):
    """
    Endpoint to generate a KoraPay virtual account for a user.
    """
    return generate_virtual_account_number(db, wallet_id=payload.wallet_id)

@router.post("/project/deposit", response_model=PlainResponse, responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def deposit_to_project_wallet(payload: ProjectWalletTransferRequest, user=Depends(auth.auth_wrapper), db: Session = Depends(get_session)):
    """
    Endpoint to transfer funds from the authenticated user's wallet to a project's wallet.
    """
    result = transfer_funds_to_project_wallet(
        db,
        user_id=user['id'],
        project_id=payload.project_id,
        amount=payload.amount,
        narration=payload.narration
    )
    if not result.get('status'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get('message')
        )
    return result

@router.post("/project/withdraw", response_model=PlainResponse, responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def withdraw_from_project_wallet(payload: ProjectWalletTransferRequest, user=Depends(auth.auth_wrapper), db: Session = Depends(get_session)):
    """
    Endpoint to transfer funds from a project's wallet back to the creator's personal wallet.
    """
    result = transfer_funds_from_project_wallet(
        db,
        user_id=user['id'],
        project_id=payload.project_id,
        amount=payload.amount,
        narration=payload.narration
    )
    if not result.get('status'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get('message')
        )
    return result