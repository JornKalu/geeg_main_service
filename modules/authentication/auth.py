from typing import Dict
from database.model import update_user, get_just_single_user_by_id, get_single_profile_by_user_id, get_single_user_by_email, get_single_user_by_username, create_user_with_relevant_rows, registration_unique_field_check, get_country_by_code, get_wallet_by_user_id, create_token, update_token, get_single_token_by_id, get_tokens, get_tokens_by_user_id, get_latest_user_token, update_token_by_user_id, update_token_by_user_id_and_token_type, update_token_email, get_latest_user_token_by_type, get_latest_user_token_by_type_and_status, get_latest_user_token_by_email_and_status, get_currency_by_code, get_social_account_by_provider, create_social_account, update_profile_by_user_id, get_social_accounts
from modules.utils.net import get_ip_info, process_phone_number, validate_email_advanced
from modules.utils.tools import process_schema_dictionary
from modules.utils.auth import AuthHandler, get_next_few_minutes, check_if_time_as_pass_now
from modules.messaging.email import e_send_token
from settings.config import load_env_config
from sqlalchemy.orm import Session
import random, datetime, sys, traceback, requests, jwt
import datetime
import random
import sys, traceback

auth = AuthHandler()
env_config = load_env_config()


def verify_social_token(provider: str, token: str):
    """
    Verifies the social token with the respective provider.
    Returns user data dictionary if valid, None otherwise.
    """
    try:
        if provider == 'google':
            response = requests.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={token}")
            if response.status_code == 200:
                data = response.json()
                # Check that the token was intended for our app
                if data.get('aud') == env_config['google_client_id']:
                    return {
                        'status': True,
                        'message': 'Success',
                        'status_code': response.status_code,
                        'data':{
                            'provider_id': data.get('sub'),
                            'email': data.get('email'),
                            'first_name': data.get('given_name'),
                            'last_name': data.get('family_name'),
                            'avatar': data.get('picture'),
                            'meta_data': data
                        },
                    }
                else:
                    return {
                        'status': False,
                        'message': f"Token not intended for app: aud - {data.get('aud')}, client_id - {env_config['google_client_id']}",
                        'status_code': response.status_code,
                        'data': None
                    }
            else:
                return {
                    'status': False,
                    'message': response.text,
                    'status_code': response.status_code,
                    'data': None
                }
        elif provider == 'x':
            # For X, we expect an OAuth 2.0 Access Token
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get("https://api.twitter.com/2/users/me?user.fields=profile_image_url", headers=headers)
            if response.status_code == 200:
                data = response.json().get('data', {})
                return {
                    'status': True,
                    'message': 'Success',
                    'status_code': response.status_code,
                    'data':{
                        'provider_id': data.get('id'),
                        'email': None, # v2 doesn't return email easily without special permissions
                        'first_name': data.get('name'),
                        'last_name': None,
                        'avatar': data.get('profile_image_url'),
                        'meta_data': data
                    }
                }
            else:
                return {
                    'status': False,
                    'message': response.text,
                    'status_code': response.status_code,
                    'data': None
                }
        elif provider == 'facebook':
            # Verify with Facebook Graph API
            fb_url = f"https://graph.facebook.com/me?fields=id,name,email,first_name,last_name,picture&access_token={token}"
            response = requests.get(fb_url)
            if response.status_code == 200:
                data = response.json()
                return {
                    'status': True,
                    'message': 'Success',
                    'status_code': response.status_code,
                    'data': {
                        'provider_id': data.get('id'),
                        'email': data.get('email'),
                        'first_name': data.get('first_name'),
                        'last_name': data.get('last_name'),
                        'avatar': data.get('picture', {}).get('data', {}).get('url'),
                        'meta_data': data
                    },
                }
            else:
                return {
                    'status': False,
                    'message': response.text,
                    'status_code': response.status_code,
                    'data': None
                }
        elif provider == 'apple':
            # For Apple, token is the id_token (JWT)
            try:
                decoded = jwt.decode(token, options={"verify_signature": False})
                if decoded.get('aud') == env_config['apple_client_id']:
                    return {
                        'status': True,
                        'message': 'Success',
                        'status_code': 200,
                        'data':{
                                'provider_id': decoded.get('sub'),
                                'email': decoded.get('email'),
                                'first_name': None, # Apple only provides name on first login via frontend
                                'last_name': None,
                                'avatar': None,
                                'meta_data': decoded
                            }
                    }
                return {
                    'status': False,
                    'message': "Apple token decryption failed",
                    'status_code': 0,
                    'data': None
                }
            except Exception as e:
                return {
                    'status': False,
                    'message': f"Social verification failed: {str(e)}",
                    'status_code': 0,
                    'data': None
                }
    except Exception as e:
        return {
            'status': False,
            'message': f"Social verification failed: {str(e)}",
            'status_code': 0,
            'data': None
        }
    return None

def register_user(db: Session, username: str = None, email: str = None, phone_number: str = None, password: str = None, first_name: str = None, last_name: str = None, is_staff: int = 0):
    country = get_country_by_code(db=db, code="NG")
    currency = get_currency_by_code(db=db, code="NGN")
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
    check = registration_unique_field_check(db=db, email=email, username=username, phone_number=phone_number)
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
        user = create_user_with_relevant_rows(db=db, phone_number=new_phone, username=username, email=email, password=hashed_password, country_id=country.id, currency_id=currency.id, first_name=first_name, last_name=last_name, is_staff=is_staff)
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
    
def create_just_user(db: Session, username: str = None, email: str = None, phone_number: str = None, password: str = None, first_name: str = None, last_name: str = None, is_staff: int = 0):
    country = get_country_by_code(db=db, code="NG")
    currency = get_currency_by_code(db=db, code="NGN")
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
        user = create_user_with_relevant_rows(db=db, phone_number=new_phone, username=username, email=email, password=hashed_password, country_id=country.id, currency_id=currency.id, first_name=first_name, last_name=last_name, is_staff=is_staff)
        return {
            'status': True,
            'message': 'Login Success',
            'data': user,
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


def authenticate_social_user(db: Session, provider: str, token: str, email: str = None):
    try:
        # 0. Backend Verification
        social_auth = verify_social_token(provider=provider, token=token)
        if social_auth['status'] == False:
            return {'status': False, 'message': f'Invalid {provider} token, message: {social_auth['message']}; status code: {social_auth['status_code']}', 'data': None}
        social_data = social_auth['data']
        provider_id = social_data['provider_id']
        email = social_data.get('email') or email
        first_name = social_data['first_name']
        last_name = social_data['last_name']
        avatar = social_data['avatar']
        meta_data = social_data['meta_data']

        if not email:
            return {'status': False, 'message': 'Email address required for registration', 'data': None}

        # 1. Try to find the social account
        social_account = get_social_account_by_provider(db=db, provider=provider, provider_id=provider_id)
        
        user = None
        if social_account:
            user = get_just_single_user_by_id(db=db, id=social_account.user_id)
        
        if not user:
            # 2. Check if a user with the same email exists
            user = get_single_user_by_email(db=db, email=email)
            
            if user:
                # Conflict Check: Ensure existing user isn't already linked to a different provider_id
                existing_links = get_social_accounts(db=db, filters={'user_id': user.id, 'provider': provider}).all()
                if existing_links and any(link.provider_id != provider_id for link in existing_links):
                    return {'status': False, 'message': f'This email is already linked to a different {provider} account', 'data': None}
            
            if not user:
                # 3. Create a new user if none exists
                country = get_country_by_code(db=db, code="NG") # Default or based on request
                user = create_user_with_relevant_rows(
                    db=db, 
                    email=email, 
                    country_id=country.id if country else None, 
                    first_name=first_name, 
                    last_name=last_name
                )
                
                # If provider provided an avatar, update the profile
                if avatar:
                    update_profile_by_user_id(db=db, user_id=user.id, values={'avatar': avatar})
            
            # 4. Link social account if not already linked (or if social_account was missing)
            if not social_account:
                create_social_account(
                    db=db, 
                    provider=provider, 
                    provider_id=provider_id, 
                    user_id=user.id, 
                    email=email, 
                    status=1, 
                    meta_data=meta_data
                )

        # 5. Standard login payload generation
        if user.status == 0:
            return {'status': False, 'message': 'Account locked', 'data': None}
        if user.deleted_at is not None:
            return {'status': False, 'message': 'Account deactivated', 'data': None}

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
        return {'status': False, 'message': str(e), 'data': None}


def get_user_details(db: Session, user_id: int=0):
    user = get_just_single_user_by_id(db=db, id=user_id)
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
    user = get_just_single_user_by_id(db=db, id=user_id)
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
    user = get_just_single_user_by_id(db=db, id=user_id)
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

def check_if_username_exists(db: Session, username: str=None):
    username_check = get_single_user_by_username(db=db, username=username)
    if username_check is not None:
        return {
            'status': True,
            'message': 'Username already exists',
            'user_id': username_check.id if username_check is not None else 0,
        }
    else:
        return {
            'status': False,
            'message': 'Username does not exists',
            'user_id': 0,
        }

def send_email_token(db: Session, email: str=None):
    validate_email = validate_email_advanced(email=email)
    if validate_email['status'] == False:
        return {
            'status': False,
            'message': validate_email['message'],
        }
    update_token_email(db=db, email=email, values={'status': 2})
    minutes = 10
    expired_at = get_next_few_minutes(minutes=minutes)
    token = str(random.randint(100000,999999))
    create_token(db=db, email=email, token_type="email", token_value=token, status=0, expired_at=expired_at)
    e_send_token(username="Geeg User", email=email, token=token, minutes=minutes)
    return {
        'status': True,
        'message': 'Success',
    }
    
def send_user_email_token(db: Session, email: str=None):
    validate_email = validate_email_advanced(email=email)
    if validate_email['status'] == False:
        return {
            'status': False,
            'message': validate_email['message'],
            'code': '02',
        }
    user = get_single_user_by_email(db=db, email=email)
    if user is None:
        return {
            'status': False,
            'message': 'User with email does not exist',
            'code': '01',
        }
    else:
        update_token_by_user_id_and_token_type(db=db, user_id=user.id, token_type="email", values={'status': 2})
        minutes = 10
        expired_at = get_next_few_minutes(minutes=minutes)
        token = str(random.randint(100000,999999))
        create_token(db=db, user_id=user.id, email=email, token_type="email", token_value=token, status=0, expired_at=expired_at)
        e_send_token(username=user.username, email=email, token=token, minutes=minutes)
        return {
            'status': True,
            'message': 'Success',
            'code': '00',
        }

def finalise_passwordless_login(db: Session, email: str=None, token_str: str=None):
    token = get_latest_user_token_by_email_and_status(db=db, email=email, token_type="email", status=0)
    if token is None:
        return {
            'status': False,
            'message': 'User has no pending email token',
            'data': None
        }
    else:
        if token.status != 0:
            return {
                'status': False,
                'message': 'Token already used',
                'data': None
            }
        if token.token_value != token_str:
            return {
                'status': False,
                'message': 'Invalid Token Value',
                'data': None
            }
        if check_if_time_as_pass_now(time_str=token.expired_at) == True:
            update_token(db=db, id=token.id, values={'status': 2})
            return {
                'status': False,
                'message': 'Token has expired',
                'data': None
            }
        user = get_single_user_by_email(db=db, email=email)
        if user is None:
            return {
                'status': False,
                'message': 'User with email does not exist',
                'data': None
            }
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

def verify_email_token(db: Session, email: str=None, token_str: str=None):
    user = get_single_user_by_email(db=db, email=email)
    if user is None:
        return {
            'status': False,
            'message': 'Email not correct',
        }
    else:
        token = get_latest_user_token_by_email_and_status(db=db, email=email, token_type="email", status=0)
        if token is None:
            return {
                'status': False,
                'message': 'User has no pending email token',
            }
        else:
            if token.status != 0:
                return {
                    'status': False,
                    'message': 'Token already used',
                }
            if token.token_value != token_str:
                return {
                    'status': False,
                    'message': 'Invalid Token Value',
                }
            if check_if_time_as_pass_now(time_str=token.expired_at) == True:
                update_token(db=db, id=token.id, values={'status': 2})
                return {
                    'status': False,
                    'message': 'Token has expired',
                }
            update_token(db=db, id=token.id, values={'status': 1})
            return {
                'status': True,
                'message': 'Success'
            }


def email_token_just_verify(db: Session, email: str=None, token_str: str=None):
    token = get_latest_user_token_by_email_and_status(db=db, email=email, token_type="email", status=0)
    if token is None:
        return {
            'status': False,
            'message': 'User has no pending email token',
        }
    else:
        if token.status != 0:
            return {
                'status': False,
                'message': 'Token already used',
            }
        if token.token_value != token_str:
            return {
                'status': False,
                'message': 'Invalid Token Value',
            }
        if check_if_time_as_pass_now(time_str=token.expired_at) == True:
            update_token(db=db, id=token.id, values={'status': 2})
            return {
                'status': False,
                'message': 'Token has expired',
            }
        update_token(db=db, id=token.id, values={'status': 1})
        return {
            'status': True,
            'message': 'Success'
        }

