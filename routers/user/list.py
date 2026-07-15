from typing import Optional, List
from fastapi import APIRouter, Request, Depends, HTTPException, Query, File, UploadFile, Form
from modules.authentication.auth import auth
from modules.users.profile import retrieve_users, retrieve_single_user
from database.schema import ErrorResponse, PlainResponse, UserDataModel, UserDataResponseModel
from database.db import get_db
from sqlalchemy.orm import Session
from fastapi_pagination import LimitOffsetPage, Page

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.get("/", response_model=Page[UserDataModel], responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def get_all(request: Request, db: Session = Depends(get_db), user=Depends(auth.auth_wrapper), username: str = Query(None), email: str = Query(None), status: int = Query(None), active: int = Query(None)):
    filters = {
        'user_type': 1
    }
    if username:
        filters['name'] = username
    if email:
        filters['email'] = email
    if status:
        filters['status'] = status
    return retrieve_users(db=db, filters=filters)

@router.get("/get_single/{user_id}", response_model=UserDataResponseModel, responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def get_single(request: Request, db: Session = Depends(get_db), user=Depends(auth.auth_wrapper), user_id: int = 0):
    return retrieve_single_user(db=db, id=user_id)
