from typing import Dict
from sqlalchemy import Column, String, BigInteger, SmallInteger, DateTime, Boolean, desc
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from database.db import Base, get_laravel_datetime


class Bank_Account(Base):
    __tablename__ = "bank_accounts"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    external_reference = Column(String(100), nullable=True) # Useful for payment provider IDs
    account_name = Column(String(150), nullable=False)
    account_number = Column(String(50), nullable=False)
    bank_name = Column(String(100), nullable=False)
    bank_code = Column(String(50), nullable=True)
    is_default = Column(Boolean, default=False)
    status = Column(SmallInteger, default=1) # 1=active, 0=inactive/unverified
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)


def create_bank_account(db: Session, user_id: int, account_name: str, account_number: str, bank_name: str, bank_code: str = None, is_default: bool = False, status: int = 1, commit: bool = False):
    bank_account = Bank_Account(
        user_id=user_id,
        account_name=account_name,
        account_number=account_number,
        bank_name=bank_name,
        bank_code=bank_code,
        is_default=is_default,
        status=status,
        created_at=get_laravel_datetime(),
        updated_at=get_laravel_datetime()
    )
    db.add(bank_account)
    if not commit:
        db.flush()
    else:
        db.commit()
        db.refresh(bank_account)
    return bank_account


def update_bank_account(db: Session, id: int = 0, values: Dict = {}, commit: bool = False):
    values['updated_at'] = get_laravel_datetime()
    db.query(Bank_Account).filter_by(id=id).update(values)
    if not commit:
        db.flush()
    else:
        db.commit()
    return True


def delete_bank_account(db: Session, id: int = 0, commit: bool = False):
    values = {
        'updated_at': get_laravel_datetime(),
        'deleted_at': get_laravel_datetime(),
    }
    db.query(Bank_Account).filter_by(id=id).update(values)
    if not commit:
        db.flush()
    else:
        db.commit()
    return True


def force_delete_bank_account(db: Session, id: int = 0, commit: bool = False):
    db.query(Bank_Account).filter_by(id=id).delete()
    if not commit:
        db.flush()
    else:
        db.commit()
    return True


def get_single_bank_account_by_id(db: Session, id: int = 0):
    return db.query(Bank_Account).filter_by(id=id).first()


def get_just_single_bank_account_by_id(db: Session, id: int = 0):
    return db.query(Bank_Account).filter_by(id=id).first()


def get_bank_accounts_by_user(db: Session, user_id: int):
    """
    Fetches all bank accounts for a specific user.
    """
    return db.query(Bank_Account).filter_by(
        user_id=user_id, 
        deleted_at=None
    ).order_by(desc(Bank_Account.is_default), desc(Bank_Account.created_at)).all()


def set_default_bank_account(db: Session, user_id: int, account_id: int, commit: bool = False):
    """
    Sets a specific bank account as default and unsets others for the same user.
    """
    # Reset all accounts for this user to false
    db.query(Bank_Account).filter_by(user_id=user_id).update({"is_default": False})
    
    # Set the chosen one to true
    db.query(Bank_Account).filter_by(id=account_id, user_id=user_id).update({"is_default": True})
    
    if commit:
        db.commit()
    else:
        db.flush()
    return True


def get_bank_accounts(db: Session, filters: Dict = {}):
    query = db.query(Bank_Account).filter(Bank_Account.deleted_at == None)
    
    if 'user_id' in filters:
        query = query.filter_by(user_id=filters['user_id'])
        
    if 'status' in filters:
        query = query.filter_by(status=filters['status'])
        
    if 'bank_name' in filters:
        query = query.filter(Bank_Account.bank_name.ilike(f"%{filters['bank_name']}%"))
        
    return query.order_by(desc(Bank_Account.created_at))