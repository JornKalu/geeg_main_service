from typing import Dict
from sqlalchemy import Column, String, BigInteger, SmallInteger, Text, DateTime, DECIMAL, desc
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from database.db import Base, get_laravel_datetime


class Role(Base):
    __tablename__ = "roles"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    project_id = Column(BigInteger, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(100), nullable=True)
    fee = Column(DECIMAL(12, 2), nullable=True)
    status = Column(SmallInteger, default=1) # 1=active, 0=inactive
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)


def create_role(db: Session, project_id: int, name: str, fee: float = 0.0, description: str = None, icon: str = None, status: int = 1, commit: bool = False):
    role = Role(
        project_id=project_id,
        name=name,
        description=description,
        icon=icon,
        fee=fee,
        status=status,
        created_at=get_laravel_datetime(),
        updated_at=get_laravel_datetime()
    )
    db.add(role)
    if not commit:
        db.flush()
    else:
        db.commit()
        db.refresh(role)
    return role


def update_role(db: Session, id: int = 0, values: Dict = {}, commit: bool = False):
    values['updated_at'] = get_laravel_datetime()
    db.query(Role).filter_by(id=id).update(values)
    if not commit:
        db.flush()
    else:
        db.commit()
    return True


def delete_role(db: Session, id: int = 0, commit: bool = False):
    values = {
        'updated_at': get_laravel_datetime(),
        'deleted_at': get_laravel_datetime(),
    }
    db.query(Role).filter_by(id=id).update(values)
    if not commit:
        db.flush()
    else:
        db.commit()
    return True


def force_delete_role(db: Session, id: int = 0, commit: bool = False):
    db.query(Role).filter_by(id=id).delete()
    if not commit:
        db.flush()
    else:
        db.commit()
    return True


def get_single_role_by_id(db: Session, id: int = 0):
    return db.query(Role).filter_by(id=id).first()


def get_roles_by_project(db: Session, project_id: int):
    """
    Fetches all roles associated with a specific project.
    """
    return db.query(Role).filter_by(
        project_id=project_id, 
        deleted_at=None
    ).order_by(Role.name.asc()).all()


def get_roles(db: Session, filters: Dict = {}):
    query = db.query(Role).filter(Role.deleted_at == None)
    
    if 'project_id' in filters:
        query = query.filter_by(project_id=filters['project_id'])
        
    if 'status' in filters:
        query = query.filter_by(status=filters['status'])
        
    if 'name' in filters:
        query = query.filter(Role.name.ilike(f"%{filters['name']}%"))
        
    return query.order_by(desc(Role.created_at))