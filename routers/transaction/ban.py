from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from database.db import get_db
from modules.transactions.bank import insert_new_bank_account, update_existing_bank_account, delete_existing_bank_account, retrieve_bank_accounts, retrieve_single_bank_account, make_bank_account_default
from database.schema import CreateBankAccountRequest, UpdateBankAccountRequest, BankAccountModel, BankAccountResponseModel, ErrorResponse, PlainResponse
from modules.authentication.auth import auth
from fastapi_pagination import Page

router = APIRouter(
    prefix="/bank-accounts",
    tags=["Bank Accounts"]
)

@router.post("/create", response_model=BankAccountResponseModel, responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def create(request: Request, fields: CreateBankAccountRequest, user=Depends(auth.auth_wrapper), db: Session = Depends(get_db)):
    return insert_new_bank_account(
        db=db, 
        user_id=user['id'], 
        account_name=fields.account_name, 
        account_number=fields.account_number, 
        bank_name=fields.bank_name, 
        bank_code=fields.bank_code, 
        is_default=fields.is_default
    )

@router.post("/update/{id}", response_model=PlainResponse, responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def update(request: Request, id: int, fields: UpdateBankAccountRequest, user=Depends(auth.auth_wrapper), db: Session = Depends(get_db)):
    values = fields.model_dump()
    result = update_existing_bank_account(db=db, id=id, user_id=user['id'], values=values)
    if not result.get('status'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.get('message'))
    return result

@router.get("/delete/{id}", response_model=PlainResponse, responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def delete(request: Request, id: int, user=Depends(auth.auth_wrapper), db: Session = Depends(get_db)):
    result = delete_existing_bank_account(db=db, id=id, user_id=user['id'])
    if not result.get('status'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.get('message'))
    return result

@router.get("/", response_model=Page[BankAccountModel], responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def get_all(request: Request, user=Depends(auth.auth_wrapper), db: Session = Depends(get_db), bank_name: str = Query(None), bank_code: str = Query(None)):
    filters = {}
    if bank_name:
        filters['bank_name'] = bank_name
    if bank_code:
        filters['bank_code'] = bank_code
    return retrieve_bank_accounts(db=db, user_id=user['id'], filters=filters)

@router.get("/get_single/{id}", response_model=BankAccountResponseModel, responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def get_single(request: Request, id: int, user=Depends(auth.auth_wrapper), db: Session = Depends(get_db)):
    result = retrieve_single_bank_account(db=db, id=id, user_id=user['id'])
    if not result.get('status'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.get('message'))
    return result

@router.get("/set-default/{id}", response_model=PlainResponse, responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def set_default(request: Request, id: int, user=Depends(auth.auth_wrapper), db: Session = Depends(get_db)):
    result = make_bank_account_default(db=db, id=id, user_id=user['id'])
    if not result.get('status'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.get('message'))
    return result