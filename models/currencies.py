from typing import Dict
from sqlalchemy import Column, String, BigInteger, SmallInteger, CHAR, DateTime, desc
from sqlalchemy.orm import Session, joinedload, selectinload, relationship
from sqlalchemy.sql import func
from database.db import Base, get_laravel_datetime


class Currency(Base):
    __tablename__ = "currencies"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    symbol = Column(String(10), nullable=False)
    code = Column(CHAR(3), nullable=False, unique=True) # ISO 4217 code (e.g., USD, NGN)
    status = Column(SmallInteger, default=1) # 1=active, 0=inactive
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    projects = relationship(
        "Project", 
        uselist=True, 
        primaryjoin="Currency.id == Project.currency_id",
        lazy="selectin"
    )

    wallets = relationship(
        "Wallet", 
        uselist=True, 
        primaryjoin="Currency.id == Wallet.currency_id",
        lazy="selectin"
    )


def create_currency(db: Session, name: str, symbol: str, code: str, status: int = 1, commit: bool = False):
    currency = Currency(
        name=name,
        symbol=symbol,
        code=code,
        status=status,
        created_at=get_laravel_datetime(),
        updated_at=get_laravel_datetime()
    )
    db.add(currency)
    if commit == False:
        db.flush()
    else:
        db.commit()
        db.refresh(currency)
    return currency


def update_currency(db: Session, id: int = 0, values: Dict = {}, commit: bool = False):
    values['updated_at'] = get_laravel_datetime()
    db.query(Currency).filter_by(id=id).update(values)
    if commit == False:
        db.flush()
    else:
        db.commit()
    return True


def delete_currency(db: Session, id: int = 0, commit: bool = False):
    values = {
        'updated_at': get_laravel_datetime(),
        'deleted_at': get_laravel_datetime(),
    }
    db.query(Currency).filter_by(id=id).update(values)
    if commit == False:
        db.flush()
    else:
        db.commit()
    return True


def force_delete_currency(db: Session, id: int = 0, commit: bool = False):
    db.query(Currency).filter_by(id=id).delete()
    if commit == False:
        db.flush()
    else:
        db.commit()
    return True


def get_single_currency_by_id(db: Session, id: int = 0):
    return db.query(Currency).filter_by(id=id).first()


def get_currency_by_code(db: Session, code: str):
    return db.query(Currency).filter_by(code=code, deleted_at=None).first()

def get_currencies(db: Session, filters: Dict = {}):
    query = db.query(Currency).filter(Currency.deleted_at == None)
    
    if 'name' in filters:
        query = query.filter(Currency.name.ilike(f"%{filters['name']}%"))
        
    if 'code' in filters:
        query = query.filter_by(code=filters['code'])
        
    if 'status' in filters:
        query = query.filter_by(status=filters['status'])
        
    return query.order_by(Currency.code.asc())