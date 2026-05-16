from typing import Dict
from sqlalchemy import Column, String, BigInteger, SmallInteger, Text, Date, DateTime, CheckConstraint, desc
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from database.db import Base, get_laravel_datetime


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, unique=True)
    country_id = Column(BigInteger, nullable=True)
    industry_id = Column(BigInteger, nullable=True)
    category_id = Column(BigInteger, nullable=True)
    first_name = Column(String(100), nullable=True)
    other_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    gender = Column(String(20), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    location = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    avatar = Column(String(500), nullable=True)
    banner = Column(String(500), nullable=True)
    status = Column(SmallInteger, default=1) # 1=active, 0=inactive
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)


def create_profile(db: Session, user_id: int, country_id: int = 0, industry_id: int = 0, category_id: int = 0, first_name: str = None, last_name: str = None, commit: bool = False):
    profile = Profile(
        user_id=user_id,
        country_id=country_id,
        industry_id=industry_id,
        category_id=category_id,
        first_name=first_name,
        last_name=last_name,
        created_at=get_laravel_datetime(),
        updated_at=get_laravel_datetime()
    )
    db.add(profile)
    if commit == False:
        db.flush()
    else:
        db.commit()
        db.refresh(profile)
    return profile


def update_profile(db: Session, id: int = 0, values: Dict = {}, commit: bool = False):
    values['updated_at'] = get_laravel_datetime()
    db.query(Profile).filter_by(id=id).update(values)
    if commit == False:
        db.flush()
    else:
        db.commit()
    return True


def delete_profile(db: Session, id: int = 0, commit: bool = False):
    values = {
        'updated_at': get_laravel_datetime(),
        'deleted_at': get_laravel_datetime(),
    }
    db.query(Profile).filter_by(id=id).update(values)
    if commit == False:
        db.flush()
    else:
        db.commit()
    return True


def force_delete_profile(db: Session, id: int = 0, commit: bool = False):
    db.query(Profile).filter_by(id=id).delete()
    if commit == False:
        db.flush()
    else:
        db.commit()
    return True


def get_single_profile_by_id(db: Session, id: int = 0):
    return db.query(Profile).filter_by(id=id).first()


def get_single_profile_by_user_id(db: Session, user_id: int):
    """
    Retrieves the profile for a specific user.
    """
    return db.query(Profile).filter_by(user_id=user_id, deleted_at=None).first()


def get_profiles(db: Session, filters: Dict = {}):
    query = db.query(Profile).filter(Profile.deleted_at == None)
    
    if 'country_id' in filters:
        query = query.filter_by(country_id=filters['country_id'])
    
    if 'industry_id' in filters:
        query = query.filter_by(industry_id=filters['industry_id'])
        
    if 'category_id' in filters:
        query = query.filter_by(category_id=filters['category_id'])
        
    if 'gender' in filters:
        query = query.filter_by(gender=filters['gender'])

    if 'name' in filters:
        search = f"%{filters['name']}%"
        query = query.filter(
            (Profile.first_name.ilike(search)) | 
            (Profile.last_name.ilike(search))
        )
        
    return query.order_by(desc(Profile.created_at))