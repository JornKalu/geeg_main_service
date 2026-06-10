from pydantic import BaseModel, Field
from typing import Optional

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