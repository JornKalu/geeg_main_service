from pydantic import BaseModel
from typing import Optional, Any

class ErrorResponse(BaseModel):
    detail: Optional[str] = None
    
    class Config:
        orm_mode = True

class PlainResponse(BaseModel):
    status: bool
    message: str
    
    class Config:
        orm_mode = True

class PlainCodeResponse(BaseModel):
    status: bool
    message: str
    code: Optional[str] = None
    
    class Config:
        orm_mode = True

class PlainResponseData(BaseModel):
    status: bool
    message: str
    data: Optional[Any] = None
    
    class Config:
        orm_mode = True
