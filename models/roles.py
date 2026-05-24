from typing import Dict
from sqlalchemy import Column, String, BigInteger, SmallInteger, Text, DateTime, DECIMAL, desc, select
from sqlalchemy.orm import Session, joinedload, selectinload, relationship
from sqlalchemy.sql import func
from sqlalchemy.sql.schema import ForeignKey
from database.db import Base, get_laravel_datetime

from .roles_users import Role_User
from .users import User

class Role(Base):
    __tablename__ = "roles"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    project_id = Column(BigInteger, ForeignKey("projects.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(100), nullable=True)
    fee = Column(DECIMAL(12, 2), nullable=True)
    status = Column(SmallInteger, default=1) # 1=active, 0=inactive
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    role_users = relationship(
        "Role_User",
        back_populates="role",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    invites = relationship(
        "Invite", 
        uselist=True, 
        primaryjoin="Role.id == Invite.role_id",
        lazy="selectin"
    )

    project = relationship(
        "Project",
        back_populates="roles"
    )


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
    return db.query(Role).options(selectinload(Role.role_users).selectinload(Role_User.user).selectinload(User.profile)).filter_by(id=id).first()

def get_just_single_role_by_id(db: Session, id: int = 0):
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
    query = db.query(Role).options(selectinload(Role.role_users).selectinload(Role_User.user).selectinload(User.profile)).filter(Role.deleted_at == None)
    
    if 'project_id' in filters:
        query = query.filter_by(project_id=filters['project_id'])
        
    if 'status' in filters:
        query = query.filter_by(status=filters['status'])
        
    if 'name' in filters:
        query = query.filter(Role.name.ilike(f"%{filters['name']}%"))
        
    return query.order_by(desc(Role.created_at))

def get_project_ids_from_roles_using_role_ids(db: Session, role_ids: list[int]):
    stmt = (
        select(Role.project_id.distinct())
        .where(
            Role.id.in_(role_ids),
            Role.deleted_at.is_(None),   # optional soft delete check
            Role.status == 1             # optional active check
        )
    )
    return db.execute(stmt).scalars().all()
