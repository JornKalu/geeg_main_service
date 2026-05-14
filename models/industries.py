from typing import Dict
from sqlalchemy import Column, String, BigInteger, SmallInteger, Text, DateTime, desc
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from database.db import Base, get_laravel_datetime


class Industry(Base):
    __tablename__ = "industries"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    status = Column(SmallInteger, default=1) # 1=active, 0=inactive
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)


def create_industry(db: Session, name: str, description: str = None, status: int = 1, commit: bool = False):
    industry = Industry(
        name=name,
        description=description,
        status=status,
        created_at=get_laravel_datetime(),
        updated_at=get_laravel_datetime()
    )
    db.add(industry)
    if commit == False:
        db.flush()
    else:
        db.commit()
        db.refresh(industry)
    return industry


def update_industry(db: Session, id: int = 0, values: Dict = {}, commit: bool = False):
    values['updated_at'] = get_laravel_datetime()
    db.query(Industry).filter_by(id=id).update(values)
    if commit == False:
        db.flush()
    else:
        db.commit()
    return True


def delete_industry(db: Session, id: int = 0, commit: bool = False):
    values = {
        'updated_at': get_laravel_datetime(),
        'deleted_at': get_laravel_datetime(),
    }
    db.query(Industry).filter_by(id=id).update(values)
    if commit == False:
        db.flush()
    else:
        db.commit()
    return True


def force_delete_industry(db: Session, id: int = 0, commit: bool = False):
    db.query(Industry).filter_by(id=id).delete()
    if commit == False:
        db.flush()
    else:
        db.commit()
    return True


def get_single_industry_by_id(db: Session, id: int = 0):
    return db.query(Industry).filter_by(id=id).first()


def get_single_industry_by_name(db: Session, name: str):
    return db.query(Industry).filter_by(name=name, deleted_at=None).first()


def get_industries(db: Session, filters: Dict = {}):
    query = db.query(Industry).filter(Industry.deleted_at == None)
    
    if 'name' in filters:
        query = query.filter(Industry.name.ilike(f"%{filters['name']}%"))
        
    if 'status' in filters:
        query = query.filter_by(status=filters['status'])
        
    return query.order_by(Industry.name.asc())