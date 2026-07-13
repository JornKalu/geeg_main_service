from typing import Dict, List, Any
from sqlalchemy.orm import Session
from database.model import create_project, update_project, delete_project, get_single_project_by_id, get_just_single_project_by_id, get_projects, create_wallet, create_role, update_role, delete_role, get_single_role_by_id, get_just_single_role_by_id, get_roles, create_role_user, check_user_has_role, create_milestone, update_milestone, delete_milestone, get_single_milestone_by_id, get_milestones, create_invite, update_invite, delete_invite, get_single_invite_by_id, get_invites, get_invite_by_email_and_project, get_single_user_by_email, get_just_single_user_by_id, get_just_single_invite_by_id, get_role_ids_from_roles_users_by_user_id, get_project_ids_from_roles_using_role_ids, get_roles_fee_sum
from modules.utils.tools import process_schema_dictionary, process_date_string
from modules.messaging.email import e_notification
from fastapi_pagination.ext.sqlalchemy import paginate

def extract_roles_total_fee(roles: List[Dict[str, Any]]):
	total_fee = 0
	if len(roles) > 0:
		for i in range(len(roles)):
			total_fee = total_fee + roles[i]['fee']
	return total_fee

def insert_new_project(db: Session, currency_id: int, name: str, start_date: str, end_date: str, created_by: int, total_fee: float = 0.0, description: str = None, roles: List[Dict[str, Any]] = []):
	start_date = process_date_string(date_str=start_date)
	end_date = process_date_string(date_str=end_date)
	total_role_fee = extract_roles_total_fee(roles=roles)
	if total_role_fee > 0:
		if total_fee != total_role_fee:
			return {
				'status': False,
				'message': f"Total project fee '{total_fee}' is not equal to total role fee '{total_role_fee}'",
				'data': None,
			}
	project = create_project(db=db, currency_id=currency_id, name=name, start_date=start_date, end_date=end_date, created_by=created_by, total_fee=total_fee, description=description, status=1)
	create_wallet(db=db, currency_id=currency_id, project_id=project.id, status=1)
	if len(roles) > 0:
		for i in range(len(roles)):
			create_role(db=db, project_id=project.id, name=roles[i]['name'], fee=roles[i]['fee'], description=roles[i]['description'], icon=roles[i]['icon'], status=1)
	return {
		'status': True,
		'message': 'Success',
		'data': project
	}

def update_existing_project(db: Session, id: int=0, values: Dict={}):
	project = get_just_single_project_by_id(db=db, id=id)
	if project is None:
		return {
			'status': False,
			'message': 'Success',
		}
	values = process_schema_dictionary(info=values)
	if 'total_fee' in values:
		project_role_fees = get_roles_fee_sum(db=db, filters={'project_id': id, 'status': 1})
		if project_role_fees > values['total_fee']:
			return {
				'status': False,
				'message': 'Total fee cannot be lower than total role fees',
			}
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

def retrieve_projects(db: Session, filters: Dict={}, user_id: int=0, active: int = 0):
	if active == 0:
		filters['created_by'] = user_id
	else:
		role_ids = get_role_ids_from_roles_users_by_user_id(db=db, user_id=user_id)
		if len(role_ids) > 0:
			project_ids = get_project_ids_from_roles_using_role_ids(db=db, role_ids=role_ids)
			if len(project_ids) > 0:
				filters['ids'] = project_ids
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
			roles_total_fee = get_roles_fee_sum(db=db, filters={'project_id': project_id, 'status': 1})
			roles_total_fee = roles_total_fee + fee
			if project.total_fee < roles_total_fee:
				return {
					'status': False,
					'message': 'Role amount exceed total project fee',
					'data': None,
				}
			role = create_role(db=db, project_id=project_id, name=name, fee=fee, description=description, icon=icon, status=1)
			return {
				'status': True,
				'message': 'Success',
				'data': role,
			}

def insert_multiple_new_role(db: Session, user_id: int, project_id: int, roles: List[Dict[str, Any]]):
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
			extracted_fee = extract_roles_total_fee(roles=roles)
			roles_total_fee = get_roles_fee_sum(db=db, filters={'project_id': project_id, 'status': 1})
			roles_total_fee = roles_total_fee + extracted_fee
			if project.total_fee < roles_total_fee:
				return {
					'status': False,
					'message': 'Roles amount exceed total project fee',
					'data': None,
				}
			resp_roles = []
			if len(roles) > 0:
				for i in range(len(roles)):
					new_role = create_role(db=db, project_id=project_id, name=roles[i]['name'], fee=roles[i]['fee'], description=roles[i]['description'], icon=roles[i]['icon'], status=1)
					resp_roles.append(new_role)
			return {
				'status': False,
				'message': 'Success',
				'data': resp_roles,
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

def delete_existing_role(db: Session, id: int=0, user_id: int = 0):
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
	start_date = process_date_string(date_str=start_date)
	end_date = process_date_string(date_str=end_date)
	milestone = create_milestone(db=db, project_id=project_id, name=name, created_by=created_by, description=description, rank=rank, start_date=start_date, end_date=end_date, assigned_to=assigned_to, status=1)
	return {
		'status': True,
		'message': 'Success',
		'data': milestone,
	}

def update_existing_milestone(db: Session, id: int=0, values: Dict={}):
	values = process_schema_dictionary(info=values)
	if 'start_date' in values:
		values['start_date'] = process_date_string(date_str=values['start_date'])
	if 'end_date' in values:
		values['end_date'] = process_date_string(date_str=values['end_date'])
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
			'message': 'Milestone not found',
			'data': None
		}
	else:
		return {
			'status': True,
			'message': 'Success',
			'data': milestone
		}


def send_invite(db: Session, user_id: int=0, project_id: int=0, role_id: int=0, email: str=None, full_name: str=None, message: str=None):
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
					'message': 'Only project creator can send invites',
					'data': None
				}
			else:
				if get_invite_by_email_and_project(db=db, email=email, project_id=project_id) == True:
					return {
						'status': False,
						'message': 'Invite has already been sent',
						'data': None,
					}
				else:
					recipient_user_id = 0
					recipient_user = get_single_user_by_email(db=db, email=email)
					if recipient_user is not None:
						recipient_user_id = recipient_user.id
					invite = create_invite(db=db, project_id=project_id, role_id=role_id, email=email, sent_by=user_id, full_name=full_name, message=message, user_id=recipient_user_id, status=0)
					sub_title = f"You have been invited to join {project.name} as a {role.name}"
					recipient_name = None
					if full_name is None:
						recipient_name = "Geeg invitee"
					else:
						recipient_name = full_name
					msg = f"You have been invited to join {project.name} as a {role.name}, login to the Geeg app or register with this email to accept the invitation."
					e_notification(email=email, title="Project Invitation", sub_title=sub_title, recipient_name=recipient_name, msg=msg)
					return {
						'status': True,
						'message': 'Success',
						'data': invite,
					}


def accept_invite(db: Session, invite_id: int=0, user_id: int=0):
	invite = get_just_single_invite_by_id(db=db, id=invite_id)
	if invite is None:
		return {
			'status': False,
			'message': 'Invite does not exists',
		}
	else:
		if invite.status != 0:
			return {
				'status': False,
				'message': 'Invite already processed',
			}
		else:
			invite_email = invite.email
			recipient_user = get_just_single_user_by_id(db=db, id=user_id)
			if recipient_user is None:
				return {
					'status': False,
					'message': 'Recipient does not exists',
				}
			else:
				if recipient_user.email != invite_email:
					return {
						'status': False,
						'message': 'Invalid invite',
					}
				else:
					sender_user = get_just_single_user_by_id(db=db, id=invite.sent_by)
					if sender_user is None:
						return {
							'status': False,
							'message': 'Sender not found',
						}
					else:
						if check_user_has_role(db=db, user_id=user_id, role_id=invite.role_id) != False:
							return {
								'status': False,
								'message': 'Role already assigned',
							}
						create_role_user(db=db, user_id=user_id, role_id=invite.role_id, status=1)
						project = get_just_single_project_by_id(db=db, id=invite.project_id)
						role = get_just_single_role_by_id(db=db, id=invite.role_id)
						update_invite(db=db, id=invite.id, values={'user_id': user_id, 'status': 1})
						sub_title = f"Your invitation for the {project.name} has been accepted"
						msg = f"{recipient_user.username} has accepted the role as {role.name} for the {project.name} project."
						e_notification(email=sender_user.email, title="Project Role Acceptance", sub_title=sub_title, recipient_name=sender_user.username, msg=msg)
						return {
							'status': True,
							'message': 'Success',
						}



def reject_invite(db: Session, invite_id: int=0, user_id: int=0):
	invite = get_just_single_invite_by_id(db=db, id=invite_id)
	if invite is None:
		return {
			'status': False,
			'message': 'Invite does not exists',
		}
	else:
		if invite.status != 0:
			return {
				'status': False,
				'message': 'Invite already processed',
			}
		else:
			invite_email = invite.email
			recipient_user = get_just_single_user_by_id(db=db, id=user_id)
			if recipient_user is None:
				return {
					'status': False,
					'message': 'Recipient does not exists',
				}
			else:
				if recipient_user.email != invite_email:
					return {
						'status': False,
						'message': 'Invalid invite',
					}
				else:
					sender_user = get_just_single_user_by_id(db=db, id=invite.sent_by)
					if sender_user is None:
						return {
							'status': False,
							'message': 'Sender not found',
						}
					else:
						project = get_just_single_project_by_id(db=db, id=invite.project_id)
						role = get_just_single_role_by_id(db=db, id=invite.role_id)
						update_invite(db=db, id=invite.id, values={'status': 2})
						sub_title = f"Your invitation for the {project.name} has been rejected"
						msg = f"{recipient_user.username} has rejected the role as {role.name} for the {project.name} project."
						e_notification(email=sender_user.email, title="Project Role Acceptance", sub_title=sub_title, recipient_name=sender_user.username, msg=msg)
						return {
							'status': True,
							'message': 'Success',
						}

def delete_existing_invite(db: Session, id: int=0, user_id: int=0):
	invite = get_just_single_invite_by_id(db=db, id=id)
	if invite is None:
		return {
			'status': False,
			'message': 'Invite does not exists',
		}
	if invite.sent_by != user_id:
		return {
			'status': False,
			'message': 'Invite can only be deleted by creator'
		}
	delete_invite(db=db, id=id)
	return {
		'status': True,
		'message': 'Success',
	}

def retrieve_invites(db: Session, filters: Dict={}):
	data = get_invites(db=db, filters=filters)
	return paginate(data)

def retrieve_single_invite(db: Session, id: int=0):
	invite = get_single_invite_by_id(db=db, id=id)
	if invite is None:
		return {
			'status': False,
			'message': 'Invite not found',
			'data': None
		}
	else:
		return {
			'status': True,
			'message': 'Success',
			'data': invite
		}