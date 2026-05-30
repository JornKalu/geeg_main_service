from typing import Dict
from sqlalchemy import Column, String, BigInteger, SmallInteger, Date, DateTime, desc
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from database.db import Base, get_laravel_datetime


class Staff(Base):
    __tablename__ = "staffs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, unique=True)
    role = Column(SmallInteger, nullable=False, default=0) # 1=superadmin, 2=admin, 3=manager, 4=support
    first_name = Column(String(100), nullable=True)
    other_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    gender = Column(String(20), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    status = Column(SmallInteger, default=0) # 1=active, 0=inactive/on-leave
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)


def create_staff(db: Session, user_id: int, role: int = 0, first_name: str = None, last_name: str = None, status: int = 1, commit: bool = False):
    staff = Staff(
        user_id=user_id,
        role=role,
        first_name=first_name,
        last_name=last_name,
        status=status,
        created_at=get_laravel_datetime(),
        updated_at=get_laravel_datetime()
    )
    db.add(staff)
    if commit == False:
        db.flush()
    else:
        db.commit()
        db.refresh(staff)
    return staff


def update_staff(db: Session, id: int = 0, values: Dict = {}, commit: bool = False):
    values['updated_at'] = get_laravel_datetime()
    db.query(Staff).filter_by(id=id).update(values)
    if commit == False:
        db.flush()
    else:
        db.commit()
    return True


def delete_staff(db: Session, id: int = 0, commit: bool = False):
    values = {
        'updated_at': get_laravel_datetime(),
        'deleted_at': get_laravel_datetime(),
    }
    db.query(Staff).filter_by(id=id).update(values)
    if commit == False:
        db.flush()
    else:
        db.commit()
    return True


def force_delete_staff(db: Session, id: int = 0, commit: bool = False):
    db.query(Staff).filter_by(id=id).delete()
    if commit == False:
        db.flush()
    else:
        db.commit()
    return True


def get_single_staff_by_id(db: Session, id: int = 0):
    return db.query(Staff).filter_by(id=id).first()


def get_staff_by_user_id(db: Session, user_id: int):
    """
    Fetches the staff profile associated with a specific user account.
    """
    return db.query(Staff).filter_by(user_id=user_id, deleted_at=None).first()


def get_staffs(db: Session, filters: Dict = {}):
    query = db.query(Staff).filter(Staff.deleted_at == None)
    
    if 'role' in filters:
        query = query.filter_by(role=filters['role'])
        
    if 'status' in filters:
        query = query.filter_by(status=filters['status'])
        
    if 'name' in filters:
        # Simple search across name fields
        search = f"%{filters['name']}%"
        query = query.filter(
            (Staff.first_name.ilike(search)) | 
            (Staff.last_name.ilike(search))
        )
        
    return query.order_by(Staff.last_name.asc())