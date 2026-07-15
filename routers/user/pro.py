from typing import Optional, List
from fastapi import APIRouter, Request, Depends, HTTPException, Query, File, UploadFile, Form
from modules.authentication.auth import auth
from modules.users.profile import update_user_profile_details
from database.schema import ErrorResponse, PlainResponse
from database.db import get_db
from sqlalchemy.orm import Session
from fastapi_pagination import LimitOffsetPage, Page

router = APIRouter(
    prefix="/profile",
    tags=["profile"]
)

@router.post("/update", response_model=PlainResponse, responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def update(request: Request, user=Depends(auth.auth_wrapper), db: Session = Depends(get_db), industry_id: int = Form(None), category_id: int = Form(None), first_name: str = Form(None), other_name: str = Form(None), last_name: str = Form(None), gender: str = Form(None), date_of_birth: str = Form(None), location: str = Form(None), bio: str = Form(None), avatar: Optional[UploadFile] = File(None), banner: Optional[UploadFile] = File(None)):
    return update_user_profile_details(db=db, avatar=avatar, banner=banner, user_id=user['id'], industry_id=industry_id, category_id=category_id, first_name=first_name, other_name=other_name, last_name=last_name, gender=gender, date_of_birth=date_of_birth, location=location, bio=bio)
