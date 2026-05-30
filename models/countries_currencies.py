from typing import Dict
from sqlalchemy import Column, BigInteger, SmallInteger, DateTime, desc
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from database.db import Base, get_laravel_datetime


class Country_Currency(Base):
    __tablename__ = "countries_currencies"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    country_id = Column(BigInteger, nullable=False)
    currency_id = Column(BigInteger, nullable=False)
    status = Column(SmallInteger, default=1) # 1=active, 0=inactive
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)


def create_country_currency(db: Session, country_id: int, currency_id: int, status: int = 1, commit: bool = False):
    pivot = Country_Currency(
        country_id=country_id,
        currency_id=currency_id,
        status=status,
        created_at=get_laravel_datetime(),
        updated_at=get_laravel_datetime()
    )
    db.add(pivot)
    if commit == False:
        db.flush()
    else:
        db.commit()
        db.refresh(pivot)
    return pivot


def update_country_currency(db: Session, id: int = 0, values: Dict = {}, commit: bool = False):
    values['updated_at'] = get_laravel_datetime()
    db.query(Country_Currency).filter_by(id=id).update(values)
    if commit == False:
        db.flush()
    else:
        db.commit()
    return True


def delete_country_currency(db: Session, id: int = 0, commit: bool = False):
    values = {
        'updated_at': get_laravel_datetime(),
        'deleted_at': get_laravel_datetime(),
    }
    db.query(Country_Currency).filter_by(id=id).update(values)
    if commit == False:
        db.flush()
    else:
        db.commit()
    return True


def force_delete_country_currency(db: Session, id: int = 0, commit: bool = False):
    db.query(Country_Currency).filter_by(id=id).delete()
    if commit == False:
        db.flush()
    else:
        db.commit()
    return True


def get_single_country_currency_by_id(db: Session, id: int = 0):
    return db.query(Country_Currency).filter_by(id=id).first()


def get_country_currencies(db: Session, filters: Dict = {}):
    query = db.query(Country_Currency).filter(Country_Currency.deleted_at == None)
    
    if 'country_id' in filters:
        query = query.filter_by(country_id=filters['country_id'])
        
    if 'currency_id' in filters:
        query = query.filter_by(currency_id=filters['currency_id'])
        
    if 'status' in filters:
        query = query.filter_by(status=filters['status'])
        
    return query.order_by(desc(Country_Currency.created_at))


# --- Utility ---
def check_country_currency_exists(db: Session, country_id: int, currency_id: int):
    """
    Checks if a link already exists between a country and currency.
    """
    return db.query(Country_Currency).filter_by(
        country_id=country_id, 
        currency_id=currency_id, 
        deleted_at=None
    ).first()