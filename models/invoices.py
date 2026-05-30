from typing import Dict
from sqlalchemy import Column, String, BigInteger, Date, DateTime, desc
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from database.db import Base, get_laravel_datetime


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    project_id = Column(BigInteger, nullable=False)
    email = Column(String(255), nullable=True)
    phone_number = Column(String(20), nullable=True)
    reference = Column(String(100), nullable=False, unique=True)
    due_date = Column(Date, nullable=True)
    status = Column(String(50), default='pending') # pending, paid, overdue, cancelled
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)


def create_invoice(db: Session, project_id: int, reference: str, email: str = None, phone_number: str = None, due_date: any = None, status: str = 'pending', commit: bool = False):
    invoice = Invoice(
        project_id=project_id,
        reference=reference,
        email=email,
        phone_number=phone_number,
        due_date=due_date,
        status=status,
        created_at=get_laravel_datetime(),
        updated_at=get_laravel_datetime()
    )
    db.add(invoice)
    if not commit:
        db.flush()
    else:
        db.commit()
        db.refresh(invoice)
    return invoice


def update_invoice(db: Session, id: int = 0, values: Dict = {}, commit: bool = False):
    values['updated_at'] = get_laravel_datetime()
    db.query(Invoice).filter_by(id=id).update(values)
    if not commit:
        db.flush()
    else:
        db.commit()
    return True


def delete_invoice(db: Session, id: int = 0, commit: bool = False):
    values = {
        'updated_at': get_laravel_datetime(),
        'deleted_at': get_laravel_datetime(),
    }
    db.query(Invoice).filter_by(id=id).update(values)
    if not commit:
        db.flush()
    else:
        db.commit()
    return True


def force_delete_invoice(db: Session, id: int = 0, commit: bool = False):
    db.query(Invoice).filter_by(id=id).delete()
    if not commit:
        db.flush()
    else:
        db.commit()
    return True


def get_single_invoice_by_id(db: Session, id: int = 0):
    return db.query(Invoice).filter_by(id=id).first()


def get_invoice_by_reference(db: Session, reference: str):
    """
    Lookup a specific invoice by its unique reference string.
    """
    return db.query(Invoice).filter_by(reference=reference, deleted_at=None).first()


def get_invoices(db: Session, filters: Dict = {}):
    query = db.query(Invoice).filter(Invoice.deleted_at == None)
    
    if 'project_id' in filters:
        query = query.filter_by(project_id=filters['project_id'])
        
    if 'status' in filters:
        query = query.filter_by(status=filters['status'])
        
    if 'email' in filters:
        query = query.filter_by(email=filters['email'])
        
    if 'reference' in filters:
        query = query.filter(Invoice.reference.ilike(f"%{filters['reference']}%"))
        
    return query.order_by(desc(Invoice.created_at))