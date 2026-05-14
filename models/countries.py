from typing import Dict
from sqlalchemy import Column, Integer, String, DateTime, BigInteger, SmallInteger, CHAR, desc
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from database.db import Base, get_laravel_datetime


class Country(Base):
    __tablename__ = "countries"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    full_name = Column(String(200), nullable=True)
    code_one = Column(CHAR(2), nullable=True) # ISO Alpha-2
    code_two = Column(CHAR(3), nullable=True) # ISO Alpha-3
    status = Column(SmallInteger, default=1) # 1=active, 0=inactive
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)


def create_country(db: Session, name: str, full_name: str = None, code_one: str = None, code_two: str = None, status: int = 1, commit: bool = False):
    country = Country(
        name=name,
        full_name=full_name,
        code_one=code_one,
        code_two=code_two,
        status=status,
        created_at=get_laravel_datetime(),
        updated_at=get_laravel_datetime()
    )
    db.add(country)
    if commit == False:
        db.flush()
    else:
        db.commit()
        db.refresh(country)
    return country


def update_country(db: Session, id: int = 0, values: Dict = {}, commit: bool = False):
    values['updated_at'] = get_laravel_datetime()
    db.query(Country).filter_by(id=id).update(values)
    if commit == False:
        db.flush()
    else:
        db.commit()
    return True


def delete_country(db: Session, id: int = 0, commit: bool = False):
    values = {
        'updated_at': get_laravel_datetime(),
        'deleted_at': get_laravel_datetime(),
    }
    db.query(Country).filter_by(id=id).update(values)
    if commit == False:
        db.flush()
    else:
        db.commit()
    return True


def force_delete_country(db: Session, id: int = 0, commit: bool = False):
    db.query(Country).filter_by(id=id).delete()
    if commit == False:
        db.flush()
    else:
        db.commit()
    return True


def get_single_country_by_id(db: Session, id: int = 0):
    return db.query(Country).filter_by(id=id).first()


def get_country_by_code(db: Session, code: str):
    """
    Search by either Alpha-2 or Alpha-3 code.
    """
    return db.query(Country).filter(
        (Country.code_one == code) | (Country.code_two == code),
        Country.deleted_at == None
    ).first()


def get_countries(db: Session, filters: Dict = {}):
    query = db.query(Country).filter(Country.deleted_at == None)
    
    if 'name' in filters:
        query = query.filter(Country.name.ilike(f"%{filters['name']}%"))
        
    if 'status' in filters:
        query = query.filter_by(status=filters['status'])
        
    return query.order_by(Country.name.asc())