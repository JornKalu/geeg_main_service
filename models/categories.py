from typing import Dict
from sqlalchemy import Column, String, BigInteger, SmallInteger, Text, DateTime, desc
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from database.db import Base, get_laravel_datetime


class Category(Base):
    __tablename__ = "categories"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    industry_id = Column(BigInteger, nullable=False)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(SmallInteger, default=1) # 1=active, 0=inactive
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)


def create_category(db: Session, industry_id: int, name: str, description: str = None, status: int = 1, commit: bool = False):
    category = Category(
        industry_id=industry_id,
        name=name,
        description=description,
        status=status,
        created_at=get_laravel_datetime(),
        updated_at=get_laravel_datetime()
    )
    db.add(category)
    if commit == False:
        db.flush()
    else:
        db.commit()
        db.refresh(category)
    return category


def update_category(db: Session, id: int = 0, values: Dict = {}, commit: bool = False):
    values['updated_at'] = get_laravel_datetime()
    db.query(Category).filter_by(id=id).update(values)
    if commit == False:
        db.flush()
    else:
        db.commit()
    return True


def delete_category(db: Session, id: int = 0, commit: bool = False):
    values = {
        'updated_at': get_laravel_datetime(),
        'deleted_at': get_laravel_datetime(),
    }
    db.query(Category).filter_by(id=id).update(values)
    if commit == False:
        db.flush()
    else:
        db.commit()
    return True


def force_delete_category(db: Session, id: int = 0, commit: bool = False):
    db.query(Category).filter_by(id=id).delete()
    if commit == False:
        db.flush()
    else:
        db.commit()
    return True


def get_single_category_by_id(db: Session, id: int = 0):
    return db.query(Category).filter_by(id=id).first()


def get_categories_by_industry_id(db: Session, industry_id: int):
    """
    Fetches all categories belonging to a specific industry.
    """
    return db.query(Category).filter_by(
        industry_id=industry_id, 
        deleted_at=None
    ).order_by(Category.name.asc()).all()


def get_categories(db: Session, filters: Dict = {}):
    query = db.query(Category).filter(Category.deleted_at == None)
    
    if 'industry_id' in filters:
        query = query.filter_by(industry_id=filters['industry_id'])
        
    if 'name' in filters:
        query = query.filter(Category.name.ilike(f"%{filters['name']}%"))
        
    if 'status' in filters:
        query = query.filter_by(status=filters['status'])
        
    return query.order_by(Category.name.asc())