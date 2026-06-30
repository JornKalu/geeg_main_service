from typing import Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, BigInteger, DECIMAL, Float, TIMESTAMP, SmallInteger, Text, desc, JSON
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from sqlalchemy.sql.expression import and_, or_
from sqlalchemy.sql.schema import ForeignKey
from database.db import Base, get_laravel_datetime, get_added_laravel_datetime, compare_laravel_datetime_with_today
from sqlalchemy.orm import relationship


class Social_Account(Base):
    __tablename__ = "social_accounts"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), default=0, nullable=True)
    provider = Column(String(255), nullable=True) # e.g., 'google', 'facebook', 'apple'
    provider_id = Column(String(255), nullable=True) # Unique ID from the provider
    email = Column(String(255), nullable=True)
    meta_data = Column(JSON, nullable=True)
    status = Column(TINYINT, default=0) # 0=inactive, 1=active
    created_at = Column(TIMESTAMP, nullable=True, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=True, server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP, nullable=True)


def create_social_account(db: Session, provider: str, provider_id: str, user_id: int = 0, email: str = None, status: int = 0, meta_data: Any = None, commit: bool = False):
    social_account = Social_Account(
        user_id=user_id,
        provider=provider,
        provider_id=provider_id,
        email=email,
        meta_data=meta_data,
        status=status,
        created_at=get_laravel_datetime(),
        updated_at=get_laravel_datetime()
    )
    db.add(social_account)
    if commit == False:
        db.flush()
    else:
        db.commit()
        db.refresh(social_account)
    return social_account


def update_social_account(db: Session, id: int = 0, values: Dict = {}, commit: bool = False):
    values['updated_at'] = get_laravel_datetime()
    db.query(Social_Account).filter_by(id=id).update(values)
    if commit == False:
        db.flush()
    else:
        db.commit()
    return True


def delete_social_account(db: Session, id: int = 0, commit: bool = False):
    values = {
        'updated_at': get_laravel_datetime(),
        'deleted_at': get_laravel_datetime(),
    }
    db.query(Social_Account).filter_by(id=id).update(values)
    if commit == False:
        db.flush()
    else:
        db.commit()
    return True


def force_delete_social_account(db: Session, id: int = 0, commit: bool = False):
    db.query(Social_Account).filter_by(id=id).delete()
    if commit == False:
        db.flush()
    else:
        db.commit()
    return True


def get_single_social_account_by_id(db: Session, id: int = 0):
    return db.query(Social_Account).filter_by(id=id).first()


def get_social_account_by_provider(db: Session, provider: str, provider_id: str):
    return db.query(Social_Account).filter_by(
        provider=provider, 
        provider_id=provider_id, 
        deleted_at=None
    ).first()


def get_social_accounts(db: Session, filters: Dict = {}):
    query = db.query(Social_Account).filter(Social_Account.deleted_at == None)
    if 'user_id' in filters:
        query = query.filter_by(user_id=filters['user_id'])
    if 'provider' in filters:
        query = query.filter_by(provider=filters['provider'])
    if 'status' in filters:
        query = query.filter_by(status=filters['status'])
    return query.order_by(desc(Social_Account.created_at))