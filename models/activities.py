from typing import Dict
from sqlalchemy import Column, String, BigInteger, SmallInteger, Text, DateTime, desc
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from database.db import Base, get_laravel_datetime


class Activity(Base):
    __tablename__ = "activities"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    action = Column(String(100), nullable=False) # e.g., 'login', 'update_profile', 'delete_project'
    description = Column(Text, nullable=True)
    status = Column(SmallInteger, default=1) # 1=success, 0=failed/warning
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)


def create_activity(db: Session, user_id: int, action: str, description: str = None, status: int = 1, commit: bool = False):
    activity = Activity(
        user_id=user_id,
        action=action,
        description=description,
        status=status,
        created_at=get_laravel_datetime(),
        updated_at=get_laravel_datetime()
    )
    db.add(activity)
    if not commit:
        db.flush()
    else:
        db.commit()
        db.refresh(activity)
    return activity


def update_activity(db: Session, id: int = 0, values: Dict = {}, commit: bool = False):
    values['updated_at'] = get_laravel_datetime()
    db.query(Activity).filter_by(id=id).update(values)
    if not commit:
        db.flush()
    else:
        db.commit()
    return True


def delete_activity(db: Session, id: int = 0, commit: bool = False):
    values = {
        'updated_at': get_laravel_datetime(),
        'deleted_at': get_laravel_datetime(),
    }
    db.query(Activity).filter_by(id=id).update(values)
    if not commit:
        db.flush()
    else:
        db.commit()
    return True


def force_delete_activity(db: Session, id: int = 0, commit: bool = False):
    db.query(Activity).filter_by(id=id).delete()
    if not commit:
        db.flush()
    else:
        db.commit()
    return True


def get_single_activity_by_id(db: Session, id: int = 0):
    return db.query(Activity).filter_by(id=id).first()


def get_activities_by_user(db: Session, user_id: int):
    """
    Retrieves the activity log for a specific user, sorted by most recent.
    """
    return db.query(Activity).filter_by(
        user_id=user_id, 
        deleted_at=None
    ).order_by(desc(Activity.created_at)).all()


def get_activities(db: Session, filters: Dict = {}):
    query = db.query(Activity).filter(Activity.deleted_at == None)
    
    if 'user_id' in filters:
        query = query.filter_by(user_id=filters['user_id'])
        
    if 'action' in filters:
        query = query.filter_by(action=filters['action'])
        
    if 'status' in filters:
        query = query.filter_by(status=filters['status'])
        
    return query.order_by(desc(Activity.created_at))