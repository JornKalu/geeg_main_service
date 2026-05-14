from typing import Dict, List
import jwt 
from fastapi import HTTPException, Security, Depends, status, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext 
from datetime import datetime, timedelta, UTC, timezone
import dateparser
import time
from settings.config import load_env_config
from database.db import get_session, get_db
from database.model import get_single_user_by_id
from sqlalchemy.orm import Session
import hashlib
import json
from authlib.integrations.starlette_client import OAuth
import sys, traceback
import os
import requests

config = load_env_config()

def get_next_few_minutes(minutes: int=0):
    current_time = datetime.now()
    future_time = current_time + timedelta(minutes=minutes)
    return future_time.strftime("%Y-%m-%d %H:%M:%S")

def check_if_time_as_pass_now(time_str: str = None):
    date_parsed = dateparser.parse(str(time_str), date_formats=['%d-%m-%Y %H:%M:%S'])
    time_tz = time.mktime(date_parsed.timetuple())
    time_tz = int(time_tz)
    current_tz = int(time.time())
    if current_tz >= time_tz:
        return True
    else:
        return False

class AuthHandler():
    security = HTTPBearer()
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    secret = config['secret_key']

    def get_password_hash(self, password: str = None):
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str=None, hashed_password: str=None):
        return self.pwd_context.verify(plain_password, hashed_password)

    def encode_token(self, db: Session, user: Dict={}):
        payload = {
            'exp': datetime.utcnow() + timedelta(days=365),
            'iat': datetime.utcnow(),
            'sub': json.dumps(user['id'])
        }
        expired_at = (datetime.utcnow() + timedelta(days=365)).strftime("%Y/%m/%d %H:%M:%S")
        token = jwt.encode(payload, self.secret, algorithm="HS256")
        if isinstance(token, bytes):
            token = token.decode('utf-8')
        return token

    def decode_token(self, db: Session, token: str = None):
        try:
            if isinstance(token, bytes):
                token = token.decode('utf-8')
            payload = jwt.decode(token, self.secret, algorithms=["HS256"])
            sub_data = json.loads(payload['sub'])
            user_id = sub_data['id']

            user = get_single_user_by_id(db=db, id=user_id)
            if user is None:
                raise HTTPException(status_code=401, detail='User does not exist')
            
            return {
                'id': user.id,
                'username': user.username,
                'phone_number': user.phone_number,
                'email': user.email,
            }
        
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail='Signature has expired')
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token:" + str(token))

    def auth_wrapper(self, db: Session = Depends(get_db), auth: HTTPAuthorizationCredentials = Security(security)):
        return self.decode_token(db, auth.credentials)

