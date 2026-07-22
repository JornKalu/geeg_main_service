from typing import Dict
from sqlalchemy import Column, String, BigInteger, Text, DateTime, DECIMAL, CheckConstraint, desc, and_, or_, SmallInteger
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from database.db import Base, get_laravel_datetime


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    from_user_id = Column(BigInteger, nullable=True)
    to_user_id = Column(BigInteger, nullable=True)
    from_wallet_id = Column(BigInteger, nullable=True)
    to_wallet_id = Column(BigInteger, nullable=True)
    invoice_id = Column(BigInteger, nullable=True)
    bank_account_id = Column(BigInteger, nullable=True)
    provider = Column(String(50), nullable=True)
    transaction_type = Column(String(30), nullable=False) # wallet_transfer, external_transfer, invoice_payment, deposit
    reference = Column(String(100), nullable=False, unique=True)
    external_reference = Column(String(100), nullable=True)
    amount = Column(DECIMAL(15, 2), nullable=False)
    fee = Column(DECIMAL(12, 2), default=0.00)
    total_amount = Column(DECIMAL(15, 2), nullable=False)
    narration = Column(Text, nullable=True)
    external_account_name = Column(String(255), nullable=True)
    external_account_number = Column(String(255), nullable=True)
    external_bank_name = Column(String(255), nullable=True)
    
    # Balance Snapshots for Audit Trail
    from_wallet_previous_balance = Column(DECIMAL(15, 2), nullable=True)
    from_wallet_new_balance = Column(DECIMAL(15, 2), nullable=True)
    to_wallet_previous_balance = Column(DECIMAL(15, 2), nullable=True)
    to_wallet_new_balance = Column(DECIMAL(15, 2), nullable=True)
    
    status = Column(SmallInteger, default=0) # 0 = pending, 1 = completed, 2 = failed, 3 = reversed
    meta_data = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "transaction_type IN ('wallet_transfer', 'external_transfer', 'invoice_payment', 'deposit')", 
            name='transaction_type_check'
        ),
    )


def create_transaction(db: Session, transaction_type: str, reference: str, amount: float, total_amount: float, values: Dict = {}, commit: bool = False):
    transaction = Transaction(
        transaction_type=transaction_type,
        reference=reference,
        amount=amount,
        total_amount=total_amount,
        **values,
        created_at=get_laravel_datetime(),
        updated_at=get_laravel_datetime()
    )
    db.add(transaction)
    if not commit:
        db.flush()
    else:
        db.commit()
        db.refresh(transaction)
    return transaction


def update_transaction(db: Session, id: int = 0, values: Dict = {}, commit: bool = False):
    values['updated_at'] = get_laravel_datetime()
    db.query(Transaction).filter_by(id=id).update(values)
    if not commit:
        db.flush()
    else:
        db.commit()
    return True


def delete_transaction(db: Session, id: int = 0, commit: bool = False):
    values = {
        'updated_at': get_laravel_datetime(),
        'deleted_at': get_laravel_datetime(),
    }
    db.query(Transaction).filter_by(id=id).update(values)
    if not commit:
        db.flush()
    else:
        db.commit()
    return True


def force_delete_transaction(db: Session, id: int = 0, commit: bool = False):
    db.query(Transaction).filter_by(id=id).delete()
    if not commit:
        db.flush()
    else:
        db.commit()
    return True


def get_single_transaction_by_id(db: Session, id: int = 0):
    return db.query(Transaction).filter_by(id=id).first()


def get_transaction_by_reference(db: Session, reference: str):
    return db.query(Transaction).filter_by(reference=reference, deleted_at=None).first()

def get_transaction_by_external_reference(db: Session, external_reference: str):
    return db.query(Transaction).filter_by(external_reference=external_reference, deleted_at=None).first()

def get_user_transaction_history(db: Session, user_id: int):
    """
    Fetches all transactions where the user was either the sender or the receiver.
    """
    return db.query(Transaction).filter(
        (Transaction.from_user_id == user_id) | (Transaction.to_user_id == user_id),
        Transaction.deleted_at == None
    ).order_by(desc(Transaction.created_at)).all()


def get_transactions(db: Session, filters: Dict = {}):
    query = db.query(Transaction).filter(Transaction.deleted_at == None)
    
    if 'status' in filters:
        query = query.filter_by(status=filters['status'])
        
    if 'transaction_type' in filters:
        query = query.filter_by(transaction_type=filters['transaction_type'])
        
    if 'invoice_id' in filters:
        query = query.filter_by(invoice_id=filters['invoice_id'])
        
    if 'bank_account_id' in filters:
        query = query.filter_by(bank_account_id=filters['bank_account_id'])
        
    if 'user_id' in filters:
        query = query.filter(or_(Transaction.from_user_id == filters['user_id'], Transaction.to_user_id == filters['user_id']))
        
    if 'wallet_id' in filters:
        query = query.filter(or_(Transaction.from_wallet_id == filters['wallet_id'], Transaction.to_wallet_id == filters['wallet_id']))
        
    return query.order_by(desc(Transaction.created_at))