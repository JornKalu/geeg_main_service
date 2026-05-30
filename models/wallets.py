from typing import Dict
from sqlalchemy import Column, BigInteger, SmallInteger, DateTime, DECIMAL, desc, UniqueConstraint
from sqlalchemy.orm import Session, joinedload, selectinload, relationship
from sqlalchemy.sql import func
from sqlalchemy.sql.schema import ForeignKey
from database.db import Base, get_laravel_datetime


class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    currency_id = Column(BigInteger, ForeignKey("currencies.id"), unique=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), unique=True)
    project_id = Column(BigInteger, ForeignKey("projects.id"), unique=True)
    balance = Column(DECIMAL(15, 2), default=0.00)
    status = Column(SmallInteger, default=1) # 1=active, 0=frozen/blocked
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    currency = relationship(
        "Currency",
        back_populates="wallets"
    )


def create_wallet(db: Session, currency_id: int = None, user_id: int = None, project_id: int = None, balance: float = 0.00, status: int = 1, commit: bool = False):
    wallet = Wallet(
        currency_id=currency_id,
        user_id=user_id,
        project_id=project_id,
        balance=balance,
        status=status,
        created_at=get_laravel_datetime(),
        updated_at=get_laravel_datetime()
    )
    db.add(wallet)
    if not commit:
        db.flush()
    else:
        db.commit()
        db.refresh(wallet)
    return wallet


def update_wallet(db: Session, id: int = 0, values: Dict = {}, commit: bool = False):
    values['updated_at'] = get_laravel_datetime()
    db.query(Wallet).filter_by(id=id).update(values)
    if not commit:
        db.flush()
    else:
        db.commit()
    return True


def delete_wallet(db: Session, id: int = 0, commit: bool = False):
    values = {
        'updated_at': get_laravel_datetime(),
        'deleted_at': get_laravel_datetime(),
    }
    db.query(Wallet).filter_by(id=id).update(values)
    if not commit:
        db.flush()
    else:
        db.commit()
    return True


def force_delete_wallet(db: Session, id: int = 0, commit: bool = False):
    db.query(Wallet).filter_by(id=id).delete()
    if not commit:
        db.flush()
    else:
        db.commit()
    return True


def get_single_wallet_by_id(db: Session, id: int = 0):
    return db.query(Wallet).filter_by(id=id).first()


def get_wallet_by_user_id(db: Session, user_id: int):
    """
    Retrieves the wallet for a specific user.
    """
    return db.query(Wallet).filter_by(user_id=user_id, deleted_at=None).first()


def get_wallet_by_project_id(db: Session, project_id: int):
    """
    Retrieves the wallet associated with a specific project.
    """
    return db.query(Wallet).filter_by(project_id=project_id, deleted_at=None).first()


def get_wallets(db: Session, filters: Dict = {}):
    query = db.query(Wallet).filter(Wallet.deleted_at == None)
    
    if 'status' in filters:
        query = query.filter_by(status=filters['status'])
        
    if 'min_balance' in filters:
        query = query.filter(Wallet.balance >= filters['min_balance'])
        
    return query.order_by(desc(Wallet.created_at))