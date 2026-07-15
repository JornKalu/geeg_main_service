from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, date

class ProfileModel(BaseModel):
    id: int
    country_id: Optional[int] = None
    industry_id: Optional[int] = None
    category_id: Optional[int] = None
    user_id: Optional[int] = None
    first_name: Optional[str] = None
    other_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    social_security: Optional[str] = None
    avatar: Optional[str] = None
    banner: Optional[str] = None
    location: Optional[str] = None
    bio: Optional[str] = None
    nin: Optional[str] = None
    bvn: Optional[str] = None
    
    class Config:
        orm_mode = True


class WalletCurrencyModel(BaseModel):
    id: int
    name: Optional[str] = None
    symbol: Optional[str] = None
    code: Optional[str] = None
    status: Optional[int] = 0
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class WalletModel(BaseModel):
    id: int
    currency_id: Optional[int] = None
    user_id: Optional[int] = None
    project_id: Optional[int] = None
    balance: Optional[float] = None
    # currency: Optional[WalletCurrencyModel] = None
    
    class Config:
        orm_mode = True

# class StaffModel(BaseModel):
#     id: int
#     user_id: int
#     first_name: Optional[str] = None
#     other_name: Optional[str] = None
#     last_name: Optional[str] = None
#     date_of_birth: Optional[str] = None
#     gender: Optional[str] = None
#     social_security: Optional[str] = None
#     department: Optional[str] = None
#     designation: Optional[str] = None
#     date_of_employment: Optional[str] = None
#     employment_status: Optional[int] = 0
#     avatar: Optional[str] = None
    
#     class Config:
#         orm_mode = True

class UserModel(BaseModel):
    id: int
    email: Optional[str] = None
    status: Optional[int] = 0
    created_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

class UserMainModel(BaseModel):
    id: int
    email: Optional[str] = None
    status: Optional[int] = 0
    profile: Optional[ProfileModel] = None
    created_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

class AuthResponseModel(BaseModel):
    access_token: Optional[str] = None
    user: Optional[UserModel] = None
    profile: Optional[ProfileModel] = None
    wallet: Optional[WalletModel] = None
    
    class Config:
        orm_mode = True


class MainAuthResponseModel(BaseModel):
    status: bool
    message: str
    data: Optional[AuthResponseModel] = None
    
    class Config:
        orm_mode = True


class UserDetailsResponseModel(BaseModel):
    user: Optional[UserModel] = None
    profile: Optional[ProfileModel] = None
    wallet: Optional[WalletModel] = None
    
    class Config:
        orm_mode = True

class MainUserDetailsResponseModel(BaseModel):
    status: bool
    message: str
    data: Optional[UserDetailsResponseModel] = None
    
    class Config:
        orm_mode = True

class UserMainResponseModel(BaseModel):
    status: bool
    message: str
    data: Optional[UserMainModel] = None
    
    class Config:
        orm_mode = True
