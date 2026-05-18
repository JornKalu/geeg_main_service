from typing import Dict
from sqlalchemy import Column, Integer, String, DateTime, BigInteger, DECIMAL, Float, TIMESTAMP, SmallInteger, Text, desc
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from sqlalchemy.sql.expression import and_, or_
from sqlalchemy.sql.schema import ForeignKey
from database.db import Base, get_laravel_datetime, get_added_laravel_datetime, compare_laravel_datetime_with_today
from sqlalchemy.orm import relationship


class Token(Base):
    __tablename__ = "tokens"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, default=0, nullable=True)
    email = Column(String(255), nullable=True)
    phone_number = Column(String(255), nullable=True)
    token_type = Column(String(255), nullable=True) # e.g., 'password_reset', 'email_verification'
    token_value = Column(String(255), nullable=True)
    status = Column(SmallInteger, default=0, nullable=True) # 0=unused/pending, 1=used, 2=expired
    expired_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, nullable=True)
    updated_at = Column(TIMESTAMP, nullable=True)
    deleted_at = Column(TIMESTAMP, nullable=True)


def create_token(db: Session, token_type: str, token_value: str, user_id: int = 0, email: str = None, phone_number: str = None, expired_at: any = None, status: int = 0, commit: bool = False):
    token = Token(
        user_id=user_id,
        email=email,
        phone_number=phone_number,
        token_type=token_type,
        token_value=token_value,
        status=status,
        expired_at=expired_at,
        created_at=get_laravel_datetime(),
        updated_at=get_laravel_datetime()
    )
    db.add(token)
    if commit == False:
        db.flush()
    else:
        db.commit()
        db.refresh(token)
    return token


def update_token(db: Session, id: int = 0, values: Dict = {}, commit: bool = False):
    values['updated_at'] = get_laravel_datetime()
    db.query(Token).filter_by(id=id).update(values)
    if commit == False:
        db.flush()
    else:
        db.commit()
    return True

def update_token_by_user_id(db: Session, user_id: int, values: Dict={}, commit: bool=False):
    values['updated_at'] = get_laravel_datetime()
    db.query(Token).filter(Token.user_id == user_id).update(values)
    if commit == False:
        db.flush()
    else:
        db.commit()
    return True

def update_token_by_user_id_and_token_type(db: Session, user_id: int=0, token_type: str=None, values: Dict={}, commit: bool=False):
    values['updated_at'] = get_laravel_datetime()
    db.query(Token).filter(and_(Token.user_id == user_id, Token.token_type == token_type)).update(values)
    if commit == False:
        db.flush()
    else:
        db.commit()
    return True

def update_token_email(db: Session, email: str=None, values: Dict={}, commit: bool=False):
    values['updated_at'] = get_laravel_datetime()
    db.query(Token).filter(Token.email == email).update(values)
    if commit == False:
        db.flush()
    else:
        db.commit()
    return True


def delete_token(db: Session, id: int = 0, commit: bool = False):
    values = {
        'updated_at': get_laravel_datetime(),
        'deleted_at': get_laravel_datetime(),
    }
    db.query(Token).filter_by(id=id).update(values)
    if commit == False:
        db.flush()
    else:
        db.commit()
    return True


def force_delete_token(db: Session, id: int = 0, commit: bool = False):
    db.query(Token).filter_by(id=id).delete()
    if commit == False:
        db.flush()
    else:
        db.commit()
    return True


def get_single_token_by_id(db: Session, id: int = 0):
    return db.query(Token).filter_by(id=id).first()


def get_tokens(db: Session, filters: Dict = {}):
    query = db.query(Token).filter(Token.deleted_at == None)
    if 'user_id' in filters:
        query = query.filter_by(user_id=filters['user_id'])
    if 'email' in filters:
        query = query.filter_by(email=filters['email'])
    if 'token_type' in filters:
        query = query.filter_by(token_type=filters['token_type'])
    if 'token_value' in filters:
        query = query.filter_by(token_value=filters['token_value'])
    if 'status' in filters:
        query = query.filter_by(status=filters['status'])
    return query.order_by(desc(Token.created_at))


def get_tokens_by_user_id(db: Session, user_id: int = 0):
    return db.query(Token).filter_by(user_device_id = user_id).filter(Token.deleted_at == None).order_by(desc(Token.id))

def get_latest_user_token(db: Session, user_id: int = 0):
    return db.query(Token).filter(and_(Token.user_id == user_id, Token.deleted_at == None)).order_by(desc(Token.id)).first()

def get_latest_user_token_by_type(db: Session, user_id: int = 0, token_type: str = None):
    return db.query(Token).filter(and_(Token.user_id == user_id, Token.token_type == token_type, Token.deleted_at == None)).order_by(desc(Token.id)).first()

def get_latest_user_token_by_type_and_status(db: Session, user_id: int = 0, token_type: str = None, status: int = 0):
    return db.query(Token).filter(and_(Token.user_id == user_id, Token.token_type == token_type, Token.status == status, Token.deleted_at == None)).order_by(desc(Token.id)).first()

def get_latest_user_token_by_email_and_status(db: Session, email: str = None, token_type: str = None, status: int = 0):
    return db.query(Token).filter(and_(Token.email == email, Token.token_type == token_type, Token.status == status, Token.deleted_at == None)).order_by(desc(Token.id)).first()

def verify_active_token(db: Session, user_id: int, token_type: str, token_value: str):
    """
    Looks for a matching, unused token for a user that has not expired yet.
    """
    return db.query(Token).filter(
        Token.user_id == user_id,
        Token.token_type == token_type,
        Token.token_value == token_value,
        Token.status == 0,
        Token.expired_at > func.now(),
        Token.deleted_at == None
    ).first()