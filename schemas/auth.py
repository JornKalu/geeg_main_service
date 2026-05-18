from pydantic import BaseModel, EmailStr
from typing import Optional, Any, Literal

class RegisterRequest(BaseModel):
    email: str
    password: str
    first_name: str
    other_name: Optional[str] = None
    last_name: str
    is_staff: Optional[int] = 0
    
    class Config:
        orm_mode = True


class LoginEmailRequest(BaseModel):
    email: EmailStr
    password: str
    
    class Config:
        orm_mode = True

class FinalisePasswordLessRequest(BaseModel):
    email: str
    token_str: str
    
    class Config:
        orm_mode = True

class SendEmailTokenRequest(BaseModel):
    email: str
    
    class Config:
        orm_mode = True

class VerifyEmailTokenRequest(BaseModel):
    email: str
    token_str: str
    
    class Config:
        orm_mode = True

class CheckEmailRequest(BaseModel):
    email: str
    
    class Config:
        orm_mode = True

class UserPinModel(BaseModel):
    pin: str
    
    class Config:
        orm_mode = True
        

class CheckUserResponseModel(BaseModel):
    status: bool
    message: str
    data: Optional[int] = None
    
    class Config:
        orm_mode = True
