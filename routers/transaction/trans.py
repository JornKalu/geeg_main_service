from typing import List, Dict
from fastapi import APIRouter, Request, Depends, HTTPException, Query
from modules.authentication.auth import auth
from modules.transactions.core import retrieve_transactions, retrieve_single_transaction
from database.schema import ErrorResponse, PlainResponse, TransactionModel, TransactionResponseModel
from database.db import get_db
from sqlalchemy.orm import Session
from fastapi_pagination import LimitOffsetPage, Page

router = APIRouter(
    prefix="/transactions",
    tags=["transactions"]
)

@router.get("/", response_model=Page[TransactionModel], responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def get_all(request: Request, db: Session = Depends(get_db), user=Depends(auth.auth_wrapper), transaction_type: str = Query(None), wallet_id: str = Query(None), status: int = Query(None), bank_account_id: int = Query(None), invoice_id: int = Query(None)):
    filters = {
        'user_id': user['id']
    }
    if transaction_type:
        filters['transaction_type'] = transaction_type
    if bank_account_id:
        filters['bank_account_id'] = bank_account_id
    if invoice_id:
        filters['invoice_id'] = invoice_id
    if wallet_id:
        filters['wallet_id'] = wallet_id
    if status:
        filters['status'] = status

    return retrieve_transactions(db=db, filters=filters)

@router.get("/get_single/{transaction_id}", response_model=TransactionResponseModel, responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def get_single(request: Request, db: Session = Depends(get_db), user=Depends(auth.auth_wrapper), transaction_id: int = 0):
    return retrieve_single_transaction(db=db, id=transaction_id)
