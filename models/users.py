from typing import Dict
from sqlalchemy import Column, String, BigInteger, SmallInteger, DateTime, CheckConstraint, desc, select
from sqlalchemy.orm import Session, joinedload, selectinload, relationship, column_property
from sqlalchemy.sql import func
from sqlalchemy.sql.expression import and_, or_
from database.db import Base, get_laravel_datetime

from .projects import Project
from .roles import Role
from .roles_users import Role_User
from .transactions import Transaction

class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    username = Column(String(80), nullable=True)
    phone_number = Column(String(20), nullable=True)
    email = Column(String(255), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    pin = Column(String(255), nullable=False)
    user_type = Column(SmallInteger, nullable=False, default=1) # 1=public, 2=staff
    status = Column(SmallInteger, default=1) # 1=active, 0=inactive
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    profile = relationship(
        "Profile", 
        uselist=False, 
        primaryjoin="User.id == Profile.user_id",
        lazy="selectin"
    )

    wallet = relationship(
        "Wallet", 
        uselist=False, 
        primaryjoin="User.id == Wallet.user_id",
        lazy="selectin"
    )

    role_users = relationship(
        "Role_User",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    projects = relationship(
        "Project",
        primaryjoin="and_(Project.deleted_at.is_(None), or_(User.id == Project.created_by, User.id.in_(select(Role_User.user_id).join(Role, Role_User.role_id == Role.id).where(Role.project_id == Project.id))))",
        viewonly=True,
        lazy="selectin"
    )

    total_projects_involved = column_property(
        select(func.count(Project.id))
        .where(
            and_(
                Project.deleted_at.is_(None),
                or_(
                    Project.created_by == id,
                    Project.id.in_(
                        select(Role.project_id)
                        .join(Role_User, Role_User.role_id == Role.id)
                        .where(
                            Role_User.user_id == id,
                            Role_User.deleted_at.is_(None),
                            Role_User.status == 1,
                            Role.deleted_at.is_(None),
                            Role.status == 1
                        )
                    )
                )
            )
        ).correlate_except(Project).scalar_subquery()
    )

    total_amount_made = column_property(
        select(func.coalesce(func.sum(Transaction.amount), 0))
        .where(
            and_(
                Transaction.to_user_id == id,
                Transaction.deleted_at.is_(None),
                Transaction.status == 1
            )
        ).correlate_except(Transaction).scalar_subquery()
    )

def create_user(db: Session, email: str, password: str, pin: str = None, username: str = None, phone_number: str = None, user_type: int = 1, status: int = 1, commit: bool = False):
    user = User(
        username=username,
        email=email,
        password=password,
        pin=pin,
        phone_number=phone_number,
        user_type=user_type,
        status=status,
        created_at=get_laravel_datetime(),
        updated_at=get_laravel_datetime()
    )
    db.add(user)
    if commit == False:
        db.flush()
    else:
        db.commit()
        db.refresh(user)
    return user


def update_user(db: Session, id: int = 0, values: Dict = {}, commit: bool = False):
    values['updated_at'] = get_laravel_datetime()
    db.query(User).filter_by(id=id).update(values)
    if commit == False:
        db.flush()
    else:
        db.commit()
    return True


def delete_user(db: Session, id: int = 0, commit: bool = False):
    values = {
        'updated_at': get_laravel_datetime(),
        'deleted_at': get_laravel_datetime(),
    }
    db.query(User).filter_by(id=id).update(values)
    if commit == False:
        db.flush()
    else:
        db.commit()
    return True


def force_delete_user(db: Session, id: int = 0, commit: bool = False):
    db.query(User).filter_by(id=id).delete()
    if commit == False:
        db.flush()
    else:
        db.commit()
    return True

def get_single_user_by_id(db: Session, id: int = 0):
    return db.query(User).options(selectinload(User.profile), selectinload(User.projects)).filter_by(id=id, deleted_at=None).first()

def get_just_single_user_by_id(db: Session, id: int = 0):
    return db.query(User).filter_by(id=id, deleted_at=None).first()

def get_single_user_by_email(db: Session, email: str):
    return db.query(User).filter_by(email=email, deleted_at=None).first()

def get_single_user_by_username(db: Session, username: str):
    return db.query(User).filter_by(username=username, deleted_at=None).first()

def get_single_user_by_phone_number(db: Session, phone_number: str):
    return db.query(User).filter_by(phone_number=phone_number, deleted_at=None).first()

def get_users(db: Session, filters: Dict = {}):
    query = db.query(User).options(selectinload(User.profile), selectinload(User.projects)).filter(User.deleted_at == None)
    
    if 'username' in filters:
        query = query.filter(User.username.ilike(f"%{filters['username']}%"))
        
    if 'phone_number' in filters:
        query = query.filter(User.phone_number.ilike(f"%{filters['phone_number']}%"))
         
    if 'email' in filters:
        query = query.filter(User.email.ilike(f"%{filters['email']}%"))
        
    if 'user_type' in filters:
        query = query.filter_by(user_type=filters['user_type'])
        
    if 'status' in filters:
        query = query.filter_by(status=filters['status'])
        
    return query.order_by(desc(User.created_at))