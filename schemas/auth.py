from pydantic import BaseModel, EmailStr
from typing import Optional, Any, Literal
from enum import Enum

class RegisterRequest(BaseModel):
    email: str
    password: str
    first_name: str
    # other_name: Optional[str] = None
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
    email: EmailStr
    token_str: str
    
    class Config:
        orm_mode = True

class SendEmailTokenRequest(BaseModel):
    email: EmailStr
    
    class Config:
        orm_mode = True

class VerifyEmailTokenRequest(BaseModel):
    email: EmailStr
    token_str: str
    
    class Config:
        orm_mode = True

class CheckEmailRequest(BaseModel):
    email: EmailStr
    
    class Config:
        orm_mode = True

class CheckUsernameRequest(BaseModel):
    username: str
    
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

class Provider(str, Enum):
    google = "google"
    facebook = "facebook"
    apple = "apple"
    x = "x"

class SocialAuthRequest(BaseModel):
    provider: Provider
    token: str
    email: Optional[str] = None
    
    class Config:
        orm_mode = True
