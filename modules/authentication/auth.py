from typing import Dict
from database.model import update_user, get_single_user_by_id, get_single_profile_by_user_id, get_single_user_by_email, get_single_staff_by_user_id, create_user_with_relevant_rows, registration_unique_field_check, create_token, update_token, get_single_token_by_id, get_tokens, get_tokens_by_user_id, get_latest_user_token, update_token_by_user_id, update_token_by_user_id_and_token_type, update_token_email, get_latest_user_token_by_type, get_latest_user_token_by_type_and_status, get_latest_user_token_by_email_and_status, get_country_by_code, get_wallet_by_user_id
from modules.utils.net import get_ip_info, process_phone_number, validate_email_advanced
from modules.utils.tools import process_schema_dictionary
from modules.utils.auth import AuthHandler, get_next_few_minutes, check_if_time_as_pass_now
from sqlalchemy.orm import Session
import random
import datetime
import random
import sys, traceback

auth = AuthHandler()


def register_user(db: Session, username: str = None, email: str = None, phone_number: str = None, password: str = None, first_name: str = None, other_name: str = None, last_name: str = None, is_staff: int = 0):
    country = get_country_by_code(db=db, code="NG")
    validate_email = validate_email_advanced(email=email)
    if validate_email['status'] == False:
        return {
            'status': False,
            'message': validate_email['message'],
            'data': None
        }
    username = str(username).strip().replace(" ", "")
    processed_phone_number = process_phone_number(phone_number=phone_number, country_code=country.code_one)
    new_phone = None
    if processed_phone_number['status'] == True:
        new_phone = processed_phone_number['phone_number']
    else:
        new_phone = phone_number
    check = registration_unique_field_check(db=db, email=email)
    if check['status'] == False:
        return {
            'status': False,
            'message': check['message'],
            'data': None,
        }
    else:
        hashed_password = None
        if password is not None:
            hashed_password = auth.get_password_hash(password=password)      
        user = create_user_with_relevant_rows(db=db, phone_number=new_phone, username=username, email=email, password=hashed_password, first_name=first_name, other_name=other_name, last_name=last_name, is_staff=is_staff)
        payload = {
            'id': user.id,
            'username': user.username,
            'phone_number': user.phone_number,
            'email': user.email,
        }
        token = auth.encode_token(db=db, user=payload)
        profile = get_single_profile_by_user_id(db=db, user_id=user.id)
        wallet = get_wallet_by_user_id(db=db, user_id=user.id)
            
        data = {
            'access_token': token,
            'user': {
                'id': user.id,
                'username': user.username,
                'phone_number': user.phone_number,
                'email': user.email,
                'status': user.status,
                'created_at': user.created_at,
            },
            'profile': profile,
            'wallet': wallet,
        }
        return {
            'status': True,
            'message': 'Login Success',
            'data': data,
        }
    

def login_with_email(db: Session, email: str=None, password: str=None):
    try:
        user = get_single_user_by_email(db=db, email=email)
        if user is None:
            return {
                'status': False,
                'message': 'Email not correct',
                'data': None
            }
        else:
            if not auth.verify_password(plain_password=password, hashed_password=user.password):
                return {
                    'status': False,
                    'message': 'Password Incorrect',
                    'data': None
                }
            else:
                if user.status == 0:
                    return {
                        'status': False,
                        'message': 'This account has been locked',
                        'data': None
                    }
                if user.deleted_at is not None:
                    return {
                        'status': False,
                        'message': 'This account has been deactivated',
                        'data': None
                    }
                payload = {
                    'id': user.id,
                    'username': user.username,
                    'phone_number': user.phone_number,
                    'email': user.email,
                }
                token = auth.encode_token(db=db, user=payload)
                profile = get_single_profile_by_user_id(db=db, user_id=user.id)
                wallet = get_wallet_by_user_id(db=db, user_id=user.id)

                data = {
                    'access_token': token,
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'phone_number': user.phone_number,
                        'email': user.email,
                        'status': user.status,
                        'created_at': user.created_at,
                    },
                    'profile': profile,
                    'wallet': wallet,
                }
                return {
                    'status': True,
                    'message': 'Login Success',
                    'data': data,
                }
    except Exception as e:
        err = "Stack Trace - %s \n" % (traceback.format_exc())
        return {
            'status': False,
            'message': err,
            'data': None
        }

def get_user_details(db: Session, user_id: int=0):
    user = get_single_user_by_id(db=db, id=user_id)
    if user is None:
        return {
            'status': False,
            'message': 'User not found',
            'data': None
        }
    else:
        profile = get_single_profile_by_user_id(db=db, user_id=user.id)
        wallet = get_wallet_by_user_id(db=db, user_id=user.id)

        data = {
            'user': {
                'id': user.id,
                'username': user.username,
                'phone_number': user.phone_number,
                'email': user.email,
                'status': user.status,
                'created_at': user.created_at,
            },
            'profile': profile,
            'wallet': wallet,
        }
        return {
            'status': True,
            'message': 'Success',
            'data': data,
        }

def update_user_pin(db: Session, user_id: int=0, pin: str=None):
    user = get_single_user_by_id(db=db, id=user_id)
    if user is None:
        return {
            'status': False,
            'message': 'User not found',
        }
    else:
        new_pin = auth.get_password_hash(password=pin)
        update_user(db=db, id=user_id, values={
            'pin': new_pin,
        })
        return {
            'status': True,
            'message': 'Success',
        }
    
def verify_user_pin(db: Session, user_id: int=0, pin: str=None):
    user = get_single_user_by_id(db=db, id=user_id)
    if user is None:
        return {
            'status': False,
            'message': 'User not found',
        }
    else:
        user_pin = user.pin
        if auth.verify_password(plain_password=pin, hashed_password=user_pin) == True:
            return {
                'status': True,
                'message': 'Correct pin',
            }
        else:
            return {
                'status': False,
                'message': 'Incorrect pin'
            }


def check_if_email_exists(db: Session, email: str=None):
    email_check = get_single_user_by_email(db=db, email=email)
    if email_check is not None:
        return {
            'status': True,
            'message': 'Email already exists',
            'user_id': email_check.id if email_check is not None else 0,
        }
    else:
        return {
            'status': False,
            'message': 'Email does not exists',
            'user_id': 0,
        }