from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

class CountryModel(BaseModel):
	id: int
	name: Optional[str] = None
	full_name: Optional[str] = None
	code_one: Optional[str] = None
	code_two: Optional[str] = None
	status: Optional[int] = 0
	created_at: Optional[datetime] = None

	class Config:
		orm_mode = True

class CountryResponseModel(BaseModel):
	status: bool
	message: str
	data: Optional[CountryModel] = None

	class Config:
		orm_mode = True


class CurrencyModel(BaseModel):
	id: int
	name: Optional[str] = None
	symbol: Optional[str] = None
	code: Optional[str] = None
	status: Optional[int] = 0
	created_at: Optional[datetime] = None

	class Config:
		orm_mode = True

class CurrencyResponseModel(BaseModel):
	status: bool
	message: str
	data: Optional[CurrencyModel] = None

	class Config:
		orm_mode = True

