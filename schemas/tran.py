from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class WalletTransferRequest(BaseModel):
    from_user_id: int = Field(..., description="The ID of the sender")
    to_user_id: int = Field(..., description="The ID of the recipient")
    amount: float = Field(..., gt=0, description="Amount to transfer")
    narration: Optional[str] = Field(None, description="Optional description for the transfer")

class GenerateVirtualAccountRequest(BaseModel):
    user_id: int = Field(..., description="The ID of the user to generate an account for")

class VirtualAccountResponseDetails(BaseModel):
    account_name: str
    account_number: str
    bank_name: str

    class Config:
        orm_mode = True

class GenerateVirtualAccountResponse(BaseModel):
    status: bool
    message: str
    data: Optional[VirtualAccountResponseDetails] = None

    class Config:
        orm_mode = True

class ProjectWalletTransferRequest(BaseModel):
    project_id: int = Field(..., description="The ID of the project wallet")
    amount: float = Field(..., gt=0, description="Amount to transfer")
    narration: Optional[str] = Field(None, description="Optional description for the transfer")

class BulkWalletTransferItem(BaseModel):
    to_user_id: int = Field(..., description="The ID of the recipient")
    amount: float = Field(..., gt=0, description="Amount to transfer")
    narration: Optional[str] = Field(None, description="Optional description for the transfer")

class BulkWalletTransferRequest(BaseModel):
    from_user_id: int = Field(..., description="The ID of the sender for all transfers")
    transfers: List[BulkWalletTransferItem] = Field(..., min_length=1, description="List of individual transfers")

class BankAccountModel(BaseModel):
    id: int
    user_id: int
    account_name: str
    account_number: str
    bank_name: str
    bank_code: str
    is_default: bool
    status: int
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class KoraBankItem(BaseModel):
    name: str
    slug: str
    code: str
    ussd: Optional[str] = None
    logo: Optional[str] = None

class KoraBankListResponse(BaseModel):
    status: bool
    message: str
    data: List[KoraBankItem]

    class Config:
        orm_mode = True

class KoraResolveAccountData(BaseModel):
    account_number: str
    account_name: str
    bank_code: str
    bank_name: str

class KoraResolveAccountResponse(BaseModel):
    status: bool
    message: str
    data: Optional[KoraResolveAccountData] = None

    class Config:
        orm_mode = True

class ResolveBankAccountRequest(BaseModel):
    bank_code: str = Field(..., description="The bank code")
    account_number: str = Field(..., description="The bank account number")

    class Config:
        orm_mode = True

class CreateBankAccountRequest(BaseModel):
    account_name: str
    account_number: str
    bank_name: str
    bank_code: str
    is_default: bool = False

    class Config:
        orm_mode = True

class UpdateBankAccountRequest(BaseModel):
    account_name: Optional[str] = None
    account_number: Optional[str] = None
    bank_name: Optional[str] = None
    bank_code: Optional[str] = None
    is_default: Optional[bool] = None

    class Config:
        orm_mode = True

class BankAccountResponseModel(BaseModel):
    status: bool
    message: str
    data: Optional[BankAccountModel] = None

    class Config:
        orm_mode = True