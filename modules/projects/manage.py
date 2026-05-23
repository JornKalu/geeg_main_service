from typing import Dict, List
from sqlalchemy.orm import Session
from database.model import create_project, update_project, delete_project, get_single_project_by_id, get_just_single_project_by_id, get_projects, create_wallet, create_role, update_role, delete_role, get_single_role_by_id, get_just_single_role_by_id, get_roles, create_role_user, check_user_has_role, create_milestone, update_milestone, delete_milestone, force_delete_milestone, get_single_milestone_by_id, get_milestones
from modules.utils.tools import process_schema_dictionary
from fastapi_pagination.ext.sqlalchemy import paginate

def insert_new_project(db: Session, currency_id: int, name: str, created_by: int, total_fee: float = 0.0, description: str = None):
	project = create_project(db=db, currency_id=currency_id, name=name, created_by=created_by, total_fee=total_fee, description=description, status=1)
	create_wallet(db=db, currency_id=currency_id, project_id=project.id, status=1)
	return {
		'status': True,
		'message': 'Success',
		'data': project
	}

def update_existing_project(db: Session, id: int=0, values: Dict={}):
	values = process_schema_dictionary(info=values)
	update_project(db=db, id=id, values=values)
	return {
		'status': True,
		'message': 'Success',
	}

def delete_existing_project(db: Session, id: int=0):
	delete_project(db=db, id=id)
	return {
		'status': True,
		'message': 'Success',
	}

def retrieve_projects(db: Session, filters: Dict={}):
	data = get_projects(db=db, filters=filters)
	return paginate(data)

def retrieve_single_project(db: Session, id: int=0):
	project = get_single_project_by_id(db=db, id=id)
	if project is None:
		return {
			'status': False,
			'message': 'Project not found',
			'data': None
		}
	else:
		return {
			'status': True,
			'message': 'Success',
			'data': project
		}

def insert_new_role(db: Session, user_id: int, project_id: int, name: str, fee: float = 0.0, description: str = None, icon: str = None):
	project = get_just_single_project_by_id(db=db, id=project_id)
	if project is None:
		return {
			'status': False,
			'message': 'Project not found',
			'data': None
		}
	else:
		if project.created_by != user_id:
			return {
			'status': False,
			'message': 'Only project creator can create roles',
			'data': None
		}
		else:
			role = insert_new_role(db=db, project_id=project_id, name=name, fee=fee, description=description, icon=icon, status=1)
			return {
				'status': True,
				'message': 'Success',
				'data': role,
			}

def update_existing_role(db: Session, user_id: int=0, id: int=0, values: Dict={}):
	role = get_just_single_role_by_id(db=db, id=id)
	if role is None:
		return {
			'status': False,
			'message': 'Role not found',
		}
	else:
		project = get_just_single_project_by_id(db=db, id=role.project_id)
		if project is None:
			return {
				'status': False,
				'message': 'Project not found',
			}
		else:
			if project.created_by != user_id:
				return {
					'status': False,
					'message': 'Only project creator can update roles',
					'data': None
				}
			else:
				values = process_schema_dictionary(info=values)
				update_role(db=db, id=id, values=values)
				return {
					'status': True,
					'message': 'Success',
				}

def delete_existing_role(db: Session, id: int=0):
	role = get_just_single_role_by_id(db=db, id=id)
	if role is None:
		return {
			'status': False,
			'message': 'Role not found',
		}
	else:
		project = get_just_single_project_by_id(db=db, id=role.project_id)
		if project is None:
			return {
				'status': False,
				'message': 'Project not found',
			}
		else:
			if project.created_by != user_id:
				return {
					'status': False,
					'message': 'Only project creator can delete roles',
					'data': None
				}
			else:
				delete_role(db=db, id=id)
				return {
					'status': True,
					'message': 'Success',
				}

def retrieve_roles(db: Session, filters: Dict={}):
	data = get_roles(db=db, filters=filters)
	return paginate(data)

def retrieve_single_role(db: Session, id: int=0):
	role = get_single_role_by_id(db=db, id=id)
	if role is None:
		return {
			'status': False,
			'message': 'Role not found',
			'data': None
		}
	else:
		return {
			'status': True,
			'message': 'Success',
			'data': role
		}

def add_user_to_role(db: Session, user_id: int=0, role_id: int=0, invite_id: int=0):
	role = get_just_single_role_by_id(db=db, id=id)
	if role is None:
		return {
			'status': False,
			'message': 'Role not found',
		}
	else:
		project = get_just_single_project_by_id(db=db, id=role.project_id)
		if project is None:
			return {
				'status': False,
				'message': 'Project not found',
			}
		else:
			if project.created_by != user_id:
				return {
					'status': False,
					'message': 'Only project creator can assign roles',
					'data': None
				}
			else:
				if check_user_has_role(db=db, user_id=user_id, role_id=role_id) != False:
					create_role_user(db=db, user_id=user_id, role_id=role_id, status=1)
				return {
					'status': True,
					'message': 'Success'
				}

def insert_new_milestone(db: Session, project_id: int, name: str, created_by: int, rank: int, start_date: str, end_date: str, description: str = None, assigned_to: int = None):
	milestone = create_milestone(db=db, project_id=project_id, name=name, created_by=created_by, description=description, rank=rank, start_date=start_date, end_date=end_date, assigned_to=assigned_to, status=1)
	return {
		'status': True,
		'message': 'Success',
		'data': milestone,
	}

def update_existing_milestone(db: Session, id: int=0, values: Dict={}):
	values = process_schema_dictionary(info=values)
	update_milestone(db=db, id=id, values=values)
	return {
		'status': True,
		'message': 'Success',
	}

def delete_existing_milestone(db: Session, id: int=0):
	delete_milestone(db=db, id=id)
	return {
		'status': True,
		'message': 'Success',
	}

def retrieve_milestones(db: Session, filters: Dict={}):
	data = get_milestones(db=db, filters=filters)
	return paginate(data)

def retrieve_single_milestone(db: Session, id: int=0):
	milestone = get_single_milestone_by_id(db=db, id=id)
	if milestone is None:
		return {
			'status': False,
			'message': 'milestone not found',
			'data': None
		}
	else:
		return {
			'status': True,
			'message': 'Success',
			'data': milestone
		}
