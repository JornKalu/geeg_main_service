from fastapi import APIRouter, Request, Depends, HTTPException
from database.db import get_session, get_db
from sqlalchemy.orm import Session
from modules.authentication.auth import auth, register_user, login_with_email, get_user_details, update_user_pin, verify_user_pin, check_if_email_exists, finalise_passwordless_login, send_email_token, send_user_email_token, verify_email_token, email_token_just_verify
from database.schema import ErrorResponse, PlainResponse, PlainCodeResponse, PlainResponseData, RegisterRequest, LoginEmailRequest, UserPinModel, MainAuthResponseModel, MainUserDetailsResponseModel, CheckUserResponseModel, CheckEmailRequest, FinalisePasswordLessRequest, SendEmailTokenRequest, VerifyEmailTokenRequest

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

@router.post("/register", response_model=MainAuthResponseModel, responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def register(request: Request, fields: RegisterRequest, db: Session = Depends(get_db)):
    req = register_user(db=db, email=fields.email, password=fields.password, first_name=fields.first_name, last_name=fields.last_name, is_staff=fields.is_staff)
    return req

@router.post("/login", response_model=MainAuthResponseModel, responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def login(request: Request, fields: LoginEmailRequest, db: Session = Depends(get_db)):
    req = login_with_email(db=db, email=fields.email, password=fields.password)
    return req

@router.post("/finalize_passwordless_login", response_model=MainAuthResponseModel, responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def login_finalize_passwordless(request: Request, fields: FinalisePasswordLessRequest, db: Session = Depends(get_db)):
    req = finalise_passwordless_login(db=db, email=fields.email, token_str=fields.token_str, fbt=fields.fbt)
    return req

@router.post("/send_token_email", response_model=PlainResponse, responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def send_token_email(request: Request, fields: SendEmailTokenRequest, db: Session = Depends(get_db)):
    req = send_email_token(db=db, email=fields.email)
    return req

@router.post("/send_user_token_email", response_model=PlainCodeResponse, responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def send_user_token_email(request: Request, fields: SendEmailTokenRequest, db: Session = Depends(get_db)):
    req = send_user_email_token(db=db, email=fields.email)
    return req

@router.post("/verify_token_email", response_model=PlainResponse, responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def verify_token_email(request: Request, fields: VerifyEmailTokenRequest, db: Session = Depends(get_db)):
    req = verify_email_token(db=db, email=fields.email, token_str=fields.token_str)
    return req

@router.post("/verify_just_email_token", response_model=PlainResponse, responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def verify_just_email_token(request: Request, fields: VerifyEmailTokenRequest, db: Session = Depends(get_db)):
    req = email_token_just_verify(db=db, email=fields.email, token_str=fields.token_str)
    return req

@router.get("/details", response_model=MainUserDetailsResponseModel, responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def details(request: Request, user=Depends(auth.auth_wrapper), db: Session = Depends(get_db)):
    return get_user_details(db=db, user_id=user['id'])

@router.post("/check_email", response_model=CheckUserResponseModel, responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def check_email(request: Request, fields: CheckEmailRequest, db: Session = Depends(get_db)):
    req = check_if_email_exists(db=db, email=fields.email)
    return req

@router.post("/update_pin", response_model=PlainResponse, responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def update_pin(request: Request, fields: UserPinModel, db: Session = Depends(get_db), user=Depends(auth.auth_wrapper)):
    req = update_user_pin(db=db, user_id=user['id'], pin=fields.pin)
    return req

@router.post("/verify_pin", response_model=PlainResponse, responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def verify_pin(request: Request, fields: UserPinModel, db: Session = Depends(get_db), user=Depends(auth.auth_wrapper)):
    req = verify_user_pin(db=db, user_id=user['id'], pin=fields.pin)
    return req
