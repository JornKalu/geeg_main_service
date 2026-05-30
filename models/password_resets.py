from typing import Dict
from sqlalchemy import Column, String, BigInteger, SmallInteger, DateTime, desc
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from database.db import Base, get_laravel_datetime


class Password_Reset(Base):
    __tablename__ = "password_resets"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    email = Column(String(255), nullable=False)
    token = Column(String(255), nullable=False)
    status = Column(SmallInteger, default=1) # 1=active/valid, 0=used/invalid
    expired_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)


def create_password_reset(db: Session, user_id: int, email: str, token: str, expired_at: any, status: int = 1, commit: bool = False):
    password_reset = Password_Reset(
        user_id=user_id,
        email=email,
        token=token,
        status=status,
        expired_at=expired_at,
        created_at=get_laravel_datetime(),
        updated_at=get_laravel_datetime()
    )
    db.add(password_reset)
    if commit == False:
        db.flush()
    else:
        db.commit()
        db.refresh(password_reset)
    return password_reset


def update_password_reset(db: Session, id: int = 0, values: Dict = {}, commit: bool = False):
    values['updated_at'] = get_laravel_datetime()
    db.query(Password_Reset).filter_by(id=id).update(values)
    if commit == False:
        db.flush()
    else:
        db.commit()
    return True


def delete_password_reset(db: Session, id: int = 0, commit: bool = False):
    values = {
        'updated_at': get_laravel_datetime(),
        'deleted_at': get_laravel_datetime(),
    }
    db.query(Password_Reset).filter_by(id=id).update(values)
    if commit == False:
        db.flush()
    else:
        db.commit()
    return True


def force_delete_password_reset(db: Session, id: int = 0, commit: bool = False):
    db.query(Password_Reset).filter_by(id=id).delete()
    if commit == False:
        db.flush()
    else:
        db.commit()
    return True


def get_single_password_reset_by_id(db: Session, id: int = 0):
    return db.query(Password_Reset).filter_by(id=id).first()


def get_password_reset_by_token(db: Session, email: str, token: str):
    """
    Finds a valid password reset record for a specific email and token.
    Useful for the actual reset verification step.
    """
    return db.query(Password_Reset).filter(
        Password_Reset.email == email,
        Password_Reset.token == token,
        Password_Reset.status == 1,
        Password_Reset.expired_at > func.now(),
        Password_Reset.deleted_at == None
    ).first()


def get_password_resets(db: Session, filters: Dict = {}):
    query = db.query(Password_Reset).filter(Password_Reset.deleted_at == None)
    
    if 'user_id' in filters:
        query = query.filter_by(user_id=filters['user_id'])
        
    if 'email' in filters:
        query = query.filter_by(email=filters['email'])
        
    if 'status' in filters:
        query = query.filter_by(status=filters['status'])
        
    return query.order_by(desc(Password_Reset.created_at))