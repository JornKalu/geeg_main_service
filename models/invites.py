from typing import Dict
from sqlalchemy import Column, String, BigInteger, Text, DateTime, desc, SmallInteger
from sqlalchemy.orm import Session, joinedload, selectinload, relationship
from sqlalchemy.sql import func
from sqlalchemy.sql.schema import ForeignKey
from database.db import Base, get_laravel_datetime


class Invite(Base):
    __tablename__ = "invites"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("user_id.id"), nullable=True) # Null if the person isn't a user yet
    project_id = Column(BigInteger, ForeignKey("projects.id"), nullable=False)
    role_id = Column(BigInteger, nullable=False)
    email = Column(String(255), nullable=False)
    full_name = Column(String(150), nullable=True)
    message = Column(Text, nullable=True)
    status = Column(SmallInteger, default=1) # pending, accepted, declined, expired
    sent_by = Column(BigInteger, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    project = relationship(
        "Project",
        back_populates="invites"
    )

    role = relationship(
        "Role",
        back_populates="invites"
    )


def create_invite(db: Session, project_id: int, role_id: int, email: str, sent_by: int, full_name: str = None, message: str = None, user_id: int = None, status: int = 0, commit: bool = False):
    invite = Invite(
        user_id=user_id,
        project_id=project_id,
        role_id=role_id,
        email=email,
        full_name=full_name,
        message=message,
        status=status,
        sent_by=sent_by,
        created_at=get_laravel_datetime(),
        updated_at=get_laravel_datetime()
    )
    db.add(invite)
    if not commit:
        db.flush()
    else:
        db.commit()
        db.refresh(invite)
    return invite


def update_invite(db: Session, id: int = 0, values: Dict = {}, commit: bool = False):
    values['updated_at'] = get_laravel_datetime()
    db.query(Invite).filter_by(id=id).update(values)
    if not commit:
        db.flush()
    else:
        db.commit()
    return True


def delete_invite(db: Session, id: int = 0, commit: bool = False):
    values = {
        'updated_at': get_laravel_datetime(),
        'deleted_at': get_laravel_datetime(),
    }
    db.query(Invite).filter_by(id=id).update(values)
    if not commit:
        db.flush()
    else:
        db.commit()
    return True


def force_delete_invite(db: Session, id: int = 0, commit: bool = False):
    db.query(Invite).filter_by(id=id).delete()
    if not commit:
        db.flush()
    else:
        db.commit()
    return True


def get_single_invite_by_id(db: Session, id: int = 0):
    return db.query(Invite).options(selectinload(Invite.project), selectinload(Invite.role)).filter_by(id=id).first()

def get_just_single_invite_by_id(db: Session, id: int = 0):
    return db.query(Invite).filter_by(id=id).first()

def get_invites(db: Session, filters: Dict = {}):
    query = db.query(Invite).options(selectinload(Invite.project), selectinload(Invite.role)).filter(Invite.deleted_at == None)
    
    if 'user_id' in filters:
        query = query.filter_by(project_id=filters['user_id'])
        
    if 'project_id' in filters:
        query = query.filter_by(project_id=filters['project_id'])
        
    if 'email' in filters:
        query = query.filter_by(email=filters['email'])
        
    if 'status' in filters:
        query = query.filter_by(status=filters['status'])
        
    if 'sent_by' in filters:
        query = query.filter_by(sent_by=filters['sent_by'])
        
    return query.order_by(desc(Invite.created_at))


# --- Utility ---
def get_invite_by_email_and_project(db: Session, email: str, project_id: int):
    """
    Check if an invite already exists for this email on this project.
    """
    return db.query(
        db.query(Invite.id)
        .filter(
            Invite.email == email,
            Invite.project_id == project_id,
            Invite.deleted_at.is_(None)
        )
        .exists()
    ).scalar()