from typing import Dict
from sqlalchemy import Column, BigInteger, SmallInteger, DateTime, desc, UniqueConstraint, select
from sqlalchemy.orm import Session, joinedload, selectinload, relationship
from sqlalchemy.sql import func
from sqlalchemy.sql.schema import ForeignKey
from database.db import Base, get_laravel_datetime


class Role_User(Base):
    __tablename__ = "roles_users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    role_id = Column(BigInteger, ForeignKey("roles.id"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    invite_id = Column(BigInteger, nullable=True)
    status = Column(SmallInteger, default=1) # 1=active, 0=inactive/suspended
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint('role_id', 'user_id', name='uq_role_user'),
    )

    role = relationship(
        "Role",
        back_populates="role_users"
    )

    user = relationship(
        "User",
        back_populates="role_users"
    )


def create_role_user(db: Session, role_id: int, user_id: int, invite_id: int = None, status: int = 1, commit: bool = False):
    role_user = Role_User(
        role_id=role_id,
        user_id=user_id,
        invite_id=invite_id,
        status=status,
        created_at=get_laravel_datetime(),
        updated_at=get_laravel_datetime()
    )
    db.add(role_user)
    if not commit:
        db.flush()
    else:
        db.commit()
        db.refresh(role_user)
    return role_user


def update_role_user(db: Session, id: int = 0, values: Dict = {}, commit: bool = False):
    values['updated_at'] = get_laravel_datetime()
    db.query(Role_User).filter_by(id=id).update(values)
    if not commit:
        db.flush()
    else:
        db.commit()
    return True


def delete_role_user(db: Session, id: int = 0, commit: bool = False):
    values = {
        'updated_at': get_laravel_datetime(),
        'deleted_at': get_laravel_datetime(),
    }
    db.query(Role_User).filter_by(id=id).update(values)
    if not commit:
        db.flush()
    else:
        db.commit()
    return True


def force_delete_role_user(db: Session, id: int = 0, commit: bool = False):
    db.query(Role_User).filter_by(id=id).delete()
    if not commit:
        db.flush()
    else:
        db.commit()
    return True


def get_single_role_user_by_id(db: Session, id: int = 0):
    return db.query(Role_User).filter_by(id=id).first()


def get_roles_users(db: Session, filters: Dict = {}):
    query = db.query(Role_User).filter(Role_User.deleted_at == None)
    
    if 'role_id' in filters:
        query = query.filter_by(role_id=filters['role_id'])
        
    if 'user_id' in filters:
        query = query.filter_by(user_id=filters['user_id'])
        
    if 'status' in filters:
        query = query.filter_by(status=filters['status'])
        
    return query.order_by(desc(Role_User.created_at))


# --- Utility ---
def get_role_ids_from_roles_users_by_user_id(db: Session, user_id: int=0):
    stmt = (
        select(Role_User.role_id)
        .where(
            Role_User.user_id == user_id,
            Role_User.deleted_at.is_(None),
            Role_User.status == 1
        )
    )
    return db.execute(stmt).scalars().all()


def check_user_has_role(db: Session, user_id: int, role_id: int):
    """
    Checks if a user is already assigned to a specific role.
    """
    return db.query(
        db.query(Role_User.id)
        .filter(
            Role_User.user_id == user_id,
            Role_User.role_id == role_id,
            Role_User.deleted_at.is_(None)
        )
        .exists()
    ).scalar()