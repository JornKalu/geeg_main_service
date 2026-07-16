from typing import Dict
from fastapi import UploadFile
from sqlalchemy.orm import Session
from database.model import update_profile_by_user_id, get_single_user_by_id, get_users
from modules.utils.tools import process_schema_dictionary, process_date_string_to_laravel
from modules.utils.net import process_phone_number
from modules.utils.files import upload_request_file_to_cloudinary
from fastapi_pagination.ext.sqlalchemy import paginate
from modules.utils.auth import AuthHandler
import json

auth = AuthHandler()

def update_user_profile_details(db: Session, avatar: UploadFile, banner: UploadFile, user_id: int=0, industry_id: int = None, category_id: int = None, first_name: str = None, other_name: str = None, last_name: str = None, gender: str = None, date_of_birth: str = None, location: str = None, bio: str = None, bvn: str = None, nin: str = None):
	pro_values = {}
	if avatar is not None:
		aupload = upload_request_file_to_cloudinary(file=avatar)
		if aupload['status'] == True:
			pro_values['avatar'] = aupload['data']['uploaded_url']
		else:
			return {
			    'status': False,
			    'message': aupload['message'],
			}
	if banner is not None:
		bupload = upload_request_file_to_cloudinary(file=banner)
		if bupload['status'] == True:
			pro_values['banner'] = bupload['data']['uploaded_url']
		else:
			return {
			    'status': False,
			    'message': bupload['message'],
			}
	if industry_id is not None:
		pro_values['industry_id'] = industry_id
	if category_id is not None:
		pro_values['category_id'] = category_id
	if first_name is not None:
		pro_values['first_name'] = first_name
	if other_name is not None:
		pro_values['other_name'] = other_name
	if last_name is not None:
		pro_values['last_name'] = last_name
	if gender is not None:
		pro_values['gender'] = gender
	if date_of_birth is not None:
		pro_values['date_of_birth'] = process_date_string_to_laravel(date_str=date_of_birth)
	if location is not None:
		pro_values['location'] = location
	if bio is not None:
		pro_values['bio'] = bio
	if bvn is not None:
		if len(bvn) != 11:
			return {
				'status': False,
				'message': 'BVN must be 11 characters long',
			}
		else:
			pro_values['bvn'] = bvn
	if nin is not None:
		pro_values['nin'] = nin
	update_profile_by_user_id(db=db, user_id=user_id, values=pro_values)
	return {
		'status': True,
		'message': 'Success',
	}

def retrieve_users(db: Session, filters: Dict={}):
	data = get_users(db=db, filters=filters)
	return paginate(data)

def retrieve_single_user(db: Session, id: int=0):
	user = get_single_user_by_id(db=db, id=id)
	if user is None:
		return {
			'status': False,
			'message': 'User not found',
			'data': None
		}
	else:
		return {
			'status': True,
			'message': 'Success',
			'data': user
		}
