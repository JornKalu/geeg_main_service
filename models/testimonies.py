from typing import Dict
from sqlalchemy import Column, String, BigInteger, SmallInteger, Text, DateTime, CheckConstraint, desc
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from database.db import Base, get_laravel_datetime


class Testimony(Base):
    __tablename__ = "testimonies"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    email = Column(String(255), nullable=True)
    rating = Column(SmallInteger, nullable=False) # 1 to 5
    feedback = Column(Text, nullable=True)
    status = Column(SmallInteger, default=1) # 1=active/approved, 0=pending/hidden
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint('rating >= 1 AND rating <= 5', name='rating_range_check'),
    )


def create_testimony(db: Session, user_id: int, rating: int, feedback: str = None, email: str = None, status: int = 1, commit: bool = False):
    testimony = Testimony(
        user_id=user_id,
        rating=rating,
        feedback=feedback,
        email=email,
        status=status,
        created_at=get_laravel_datetime(),
        updated_at=get_laravel_datetime()
    )
    db.add(testimony)
    if not commit:
        db.flush()
    else:
        db.commit()
        db.refresh(testimony)
    return testimony


def update_testimony(db: Session, id: int = 0, values: Dict = {}, commit: bool = False):
    values['updated_at'] = get_laravel_datetime()
    db.query(Testimony).filter_by(id=id).update(values)
    if not commit:
        db.flush()
    else:
        db.commit()
    return True


def delete_testimony(db: Session, id: int = 0, commit: bool = False):
    values = {
        'updated_at': get_laravel_datetime(),
        'deleted_at': get_laravel_datetime(),
    }
    db.query(Testimony).filter_by(id=id).update(values)
    if not commit:
        db.flush()
    else:
        db.commit()
    return True


def force_delete_testimony(db: Session, id: int = 0, commit: bool = False):
    db.query(Testimony).filter_by(id=id).delete()
    if not commit:
        db.flush()
    else:
        db.commit()
    return True


def get_single_testimony_by_id(db: Session, id: int = 0):
    return db.query(Testimony).filter_by(id=id).first()


def get_approved_testimonies(db: Session, limit: int = 10):
    """
    Fetches the latest approved/active testimonies for display.
    """
    return db.query(Testimony).filter_by(
        status=1, 
        deleted_at=None
    ).order_by(desc(Testimony.created_at)).limit(limit).all()


def get_testimonies(db: Session, filters: Dict = {}):
    query = db.query(Testimony).filter(Testimony.deleted_at == None)
    
    if 'user_id' in filters:
        query = query.filter_by(user_id=filters['user_id'])
        
    if 'status' in filters:
        query = query.filter_by(status=filters['status'])
        
    if 'min_rating' in filters:
        query = query.filter(Testimony.rating >= filters['min_rating'])
        
    return query.order_by(desc(Testimony.created_at))