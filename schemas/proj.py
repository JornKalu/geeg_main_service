from typing import Optional, List, Dict
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from .user import UserMainModel, WalletModel, WalletCurrencyModel

class RoleUserModel(BaseModel):
	id: int
	role_id: Optional[int] = None
	user_id: Optional[int] = None
	invite_id: Optional[int] = None
	status: Optional[int] = None
	user: Optional[UserMainModel] = None

	class Config:
		orm_mode = True

class RoleModel(BaseModel):
	id: int
	project_id: Optional[int] = None
	name: Optional[str] = None
	description: Optional[str] = None
	icon: Optional[str] = None
	fee: Optional[float] = None
	status: Optional[int] = None
	role_users: Optional[RoleUserModel] = None
	created_at: Optional[datetime] = None

	class Config:
		orm_mode = True


class MilestoneModel(BaseModel):
	id: int
	project_id: Optional[int] = None
	name: Optional[str] = None
	description: Optional[str] = None
	rank: Optional[int] = None
	start_date: Optional[str] = None
	end_date: Optional[str] = None
	status: Optional[int] = None
	assigned_to: Optional[int] = None
	created_by: Optional[int] = None
	created_at: Optional[datetime] = None

	class Config:
		orm_mode = True

class ProjectModel(BaseModel):
	id: int
	currency_id: Optional[int] = None
	name: Optional[str] = None
	description: Optional[str] = None
	start_date: Optional[str] = None
	end_date: Optional[str] = None
	total_fee: Optional[float] = None
	status: Optional[int] = None
	created_by: Optional[int] = None
	created_at: Optional[datetime] = None
	currency: Optional[WalletCurrencyModel] = None
	wallet: Optional[WalletModel] = None
	milestones: Optional[List[MilestoneModel]] = None

	class Config:
		orm_mode = True


class CreateProjectRoleModel(BaseModel):
	name: str
	fee: float
	description: Optional[str] = None
	icon: Optional[str] = None

	class Config:
		orm_mode = True

class CreateProjectModel(BaseModel):
	currency_id: int
	name: str
	start_date: str
	end_date: str
	total_fee: float
	description: Optional[str] = None
	roles: List[CreateProjectRoleModel] = Field(default_factory=list, description="List of roles to be created with the project")

	class Config:
		orm_mode = True

class UpdateProjectModel(BaseModel):
	name: Optional[str] = None
	total_fee: Optional[float] = None
	description: Optional[str] = None

	class Config:
		orm_mode = True


class ProjectResponseModel(BaseModel):
	status: bool
	message: str
	data: Optional[ProjectModel] = None

	class Config:
		orm_mode = True

class CreateRoleModel(BaseModel):
	project_id: int
	name: str
	fee: float
	description: Optional[str] = None
	icon: Optional[str] = None

	class Config:
		orm_mode = True

class UpdateRoleModel(BaseModel):
	name: Optional[str] = None
	fee: Optional[float] = None
	description: Optional[str] = None
	icon: Optional[str] = None

	class Config:
		orm_mode = True

class RoleResponseModel(BaseModel):
	status: bool
	message: str
	data: Optional[RoleModel] = None

	class Config:
		orm_mode = True

class CreateMilestoneModel(BaseModel):
	project_id: int
	name: str
	rank: int
	start_date: str
	end_date: str
	description: Optional[str] = None
	assigned_to: Optional[int] = None

	class Config:
		orm_mode = True

class UpdateMilestoneModel(BaseModel):
	name: Optional[str] = None
	rank: Optional[int] = None
	start_date: Optional[str] = None
	end_date: Optional[str] = None
	description: Optional[str] = None
	assigned_to: Optional[int] = None

	class Config:
		orm_mode = True

class MilestoneResponseModel(BaseModel):
	status: bool
	message: str
	data: Optional[MilestoneModel] = None

	class Config:
		orm_mode = True

class AddUserToRoleModel(BaseModel):
	user_id: int
	role_id: int
	invite_id: Optional[int] = 0

	class Config:
		orm_mode = True


class InviteModel(BaseModel):
	id: int
	user_id: Optional[int] = None
	project_id: Optional[int] = None
	role_id: Optional[int] = None
	email: Optional[str] = None
	full_name: Optional[str] = None
	message: Optional[str] = None
	status: Optional[int] = None
	sent_by: Optional[int] = None
	created_at: Optional[datetime] = None
	project: Optional[ProjectModel] = None
	role: Optional[RoleModel] = None

	class Config:
		orm_mode = True

class InviteResponseModel(BaseModel):
	status: bool
	message: str
	data: Optional[InviteModel] = None

	class Config:
		orm_mode = True

class SendInviteModel(BaseModel):
	project_id: int
	role_id: int
	email: EmailStr
	full_name: Optional[str] = None
	message: Optional[str] = None

	class Config:
		orm_mode = True

class AcceptInviteModel(BaseModel):
	invite_id: int

	class Config:
		orm_mode = True

class RejectInviteModel(BaseModel):
	invite_id: int

	class Config:
		orm_mode = True
