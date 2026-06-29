from typing import List, Dict
from fastapi import APIRouter, Request, Depends, HTTPException, Query
from modules.authentication.auth import auth
from modules.projects.manage import insert_new_project, update_existing_project, delete_existing_project, retrieve_projects, retrieve_single_project, insert_new_role, insert_multiple_new_role, update_existing_role, delete_existing_role, retrieve_roles, retrieve_single_role, add_user_to_role, insert_new_milestone, update_existing_milestone, delete_existing_milestone, retrieve_milestones, retrieve_single_milestone, send_invite, accept_invite, reject_invite, delete_existing_invite, retrieve_invites, retrieve_single_invite
from database.schema import ErrorResponse, PlainResponse, RoleModel, MilestoneModel, ProjectModel, CreateProjectModel, UpdateProjectModel, ProjectResponseModel, CreateRoleModel, UpdateRoleModel, RoleResponseModel, CreateMilestoneModel, UpdateMilestoneModel, MilestoneResponseModel, AddUserToRoleModel, InviteModel, InviteResponseModel, SendInviteModel, AcceptInviteModel, RejectInviteModel, CreateMultipleRoleModel, MultipleRoleResponseModel
from database.db import get_db
from sqlalchemy.orm import Session
from fastapi_pagination import LimitOffsetPage, Page

router = APIRouter(
    prefix="/projects",
    tags=["projects"]
)


@router.post("/create", response_model=ProjectResponseModel, responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def create(request: Request, fields: CreateProjectModel, user=Depends(auth.auth_wrapper), db: Session = Depends(get_db)):
    roles = []
    if fields.roles != []:
        roles = [t.model_dump() for t in fields.roles]
    req = insert_new_project(db=db, currency_id=fields.currency_id, name=fields.name, start_date=fields.start_date, end_date=fields.end_date, created_by=user['id'], total_fee=fields.total_fee, description=fields.description, roles=roles)
    return req

@router.post("/update/{project_id}", response_model=PlainResponse, responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def update(request: Request, fields: UpdateProjectModel, user=Depends(auth.auth_wrapper), db: Session = Depends(get_db), project_id: int=0):
    values = fields.model_dump()
    req = update_existing_project(db=db, id=project_id, values=values)
    return req

@router.get("/delete/{project_id}", response_model=PlainResponse, responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def delete(request: Request, user=Depends(auth.auth_wrapper), db: Session = Depends(get_db), project_id: int = 0):
    return delete_existing_project(db=db, id=project_id)

@router.get("/", response_model=Page[ProjectModel], responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def get_all(request: Request, db: Session = Depends(get_db), user=Depends(auth.auth_wrapper), name: str = Query(None), currency_id: str = Query(None), status: int = Query(None), active: int = Query(None)):
    filters = {}
    if name:
        filters['name'] = name
    if currency_id:
        filters['currency_id'] = currency_id
    if status:
        filters['status'] = status
    return retrieve_projects(db=db, filters=filters, user_id=user['id'], active=active)

@router.get("/get_single/{project_id}", response_model=ProjectResponseModel, responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def get_single(request: Request, db: Session = Depends(get_db), user=Depends(auth.auth_wrapper), project_id: int = 0):
    return retrieve_single_project(db=db, id=project_id)

@router.post("/roles/create", response_model=RoleResponseModel, responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def roles_create(request: Request, fields: CreateRoleModel, user=Depends(auth.auth_wrapper), db: Session = Depends(get_db)):
    req = insert_new_role(db=db, user_id=user['id'], project_id=fields.project_id, name=fields.name, fee=fields.fee, description=fields.description, icon=fields.icon)
    return req

@router.post("/roles/create_multiple", response_model=MultipleRoleResponseModel, responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def roles_create_multiple(request: Request, fields: CreateMultipleRoleModel, user=Depends(auth.auth_wrapper), db: Session = Depends(get_db)):
    req = insert_multiple_new_role(db=db, user_id=user['id'], project_id=fields.project_id, roles=fields.roles)
    return req

@router.post("/roles/update/{role_id}", response_model=PlainResponse, responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def roles_update(request: Request, fields: UpdateRoleModel, user=Depends(auth.auth_wrapper), db: Session = Depends(get_db), role_id: int=0):
    values = fields.model_dump()
    req = update_existing_role(db=db, id=role_id, values=values)
    return req

@router.get("/roles/delete/{role_id}", response_model=PlainResponse, responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def roles_delete(request: Request, user=Depends(auth.auth_wrapper), db: Session = Depends(get_db), role_id: int = 0):
    return delete_existing_role(db=db, id=role_id, user_id=user['id'])

@router.get("/roles", response_model=Page[RoleModel], responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def roles_get_all(request: Request, db: Session = Depends(get_db), user=Depends(auth.auth_wrapper), name: str = Query(None), project_id: int = Query(None), status: int = Query(None)):
    filters = {}
    if name:
        filters['name'] = name
    if project_id:
        filters['project_id'] = project_id
    if status:
        filters['status'] = status
    return retrieve_roles(db=db, filters=filters)

@router.get("/roles/get_single/{role_id}", response_model=RoleResponseModel, responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def roles_get_single(request: Request, db: Session = Depends(get_db), user=Depends(auth.auth_wrapper), role_id: int = 0):
    return retrieve_single_role(db=db, id=role_id)

@router.post("/milestones/create", response_model=MilestoneResponseModel, responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def milestones_create(request: Request, fields: CreateMilestoneModel, user=Depends(auth.auth_wrapper), db: Session = Depends(get_db)):
    req = insert_new_milestone(db=db, created_by=user['id'], project_id=fields.project_id, name=fields.name, rank=fields.rank, description=fields.description, start_date=fields.start_date, end_date=fields.end_date, assigned_to=fields.assigned_to)
    return req

@router.post("/milestones/update/{milestone_id}", response_model=PlainResponse, responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def milestones_update(request: Request, fields: UpdateRoleModel, user=Depends(auth.auth_wrapper), db: Session = Depends(get_db), milestone_id: int=0):
    values = fields.model_dump()
    req = update_existing_milestone(db=db, id=milestone_id, values=values)
    return req

@router.get("/milestones/delete/{milestone_id}", response_model=PlainResponse, responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def milestones_delete(request: Request, user=Depends(auth.auth_wrapper), db: Session = Depends(get_db), milestone_id: int = 0):
    return delete_existing_milestone(db=db, id=milestone_id)

@router.get("/milestones", response_model=Page[MilestoneModel], responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def milestones_get_all(request: Request, db: Session = Depends(get_db), user=Depends(auth.auth_wrapper), name: str = Query(None), project_id: int = Query(None), status: int = Query(None)):
    filters = {}
    if name:
        filters['name'] = name
    if project_id:
        filters['project_id'] = project_id
    if status:
        filters['status'] = status
    return retrieve_milestones(db=db, filters=filters)

@router.get("/milestones/get_single/{milestone_id}", response_model=MilestoneResponseModel, responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def milestones_get_single(request: Request, db: Session = Depends(get_db), user=Depends(auth.auth_wrapper), milestone_id: int = 0):
    return retrieve_single_milestone(db=db, id=milestone_id)

@router.post("/invites/send", response_model=InviteResponseModel, responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def invites_send(request: Request, fields: SendInviteModel, user=Depends(auth.auth_wrapper), db: Session = Depends(get_db)):
    req = send_invite(db=db, created_by=user['id'], project_id=fields.project_id, role_id=fields.role_id, email=fields.email, full_name=fields.full_name, message=fields.message)
    return req

@router.post("/invites/accept", response_model=PlainResponse, responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def invites_accept(request: Request, fields: AcceptInviteModel, user=Depends(auth.auth_wrapper), db: Session = Depends(get_db)):
    req = accept_invite(db=db, user_id=user['id'], invite_id=fields.invite_id)
    return req

@router.post("/invites/reject", response_model=PlainResponse, responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def invites_reject(request: Request, fields: RejectInviteModel, user=Depends(auth.auth_wrapper), db: Session = Depends(get_db)):
    req = reject_invite(db=db, user_id=user['id'], invite_id=fields.invite_id)
    return req

@router.get("/invites/delete/{invite_id}", response_model=PlainResponse, responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def invites_delete(request: Request, user=Depends(auth.auth_wrapper), db: Session = Depends(get_db), invite_id: int = 0):
    return delete_existing_invite(db=db, id=invite_id, user_id=user['id'])

@router.get("/invites", response_model=Page[InviteModel], responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def invites_get_all(request: Request, db: Session = Depends(get_db), user=Depends(auth.auth_wrapper), project_id: int = Query(None), sent_by: int = Query(None), status: int = Query(None)):
    filters = {}
    if project_id:
        filters['project_id'] = project_id
    if sent_by:
        filters['sent_by'] = sent_by
    else:
        filters['email'] = user['email']
    if status:
        filters['status'] = status
    return retrieve_invites(db=db, filters=filters)

@router.get("/invites/get_single/{invite_id}", response_model=InviteResponseModel, responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def invites_get_single(request: Request, db: Session = Depends(get_db), user=Depends(auth.auth_wrapper), invite_id: int = 0):
    return retrieve_single_invite(db=db, id=invite_id)


