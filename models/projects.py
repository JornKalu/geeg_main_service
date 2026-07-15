from typing import Dict
from sqlalchemy import Column, String, BigInteger, SmallInteger, Text, Date, DateTime, DECIMAL, desc
from sqlalchemy.orm import Session, joinedload, selectinload, relationship
from sqlalchemy.sql import func
from sqlalchemy.sql.schema import ForeignKey
from database.db import Base, get_laravel_datetime

from .roles import Role
from .roles_users import Role_User

class Project(Base):
    __tablename__ = "projects"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    currency_id = Column(BigInteger, ForeignKey("currencies.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    total_fee = Column(DECIMAL(15, 2), nullable=True)
    status = Column(SmallInteger, default=1) # 1=active, 0=inactive/draft
    created_by = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    roles = relationship(
        "Role", 
        uselist=True, 
        primaryjoin="Project.id == Role.project_id",
        lazy="selectin"
    )

    milestones = relationship(
        "Milestone", 
        uselist=True, 
        primaryjoin="Project.id == Milestone.project_id",
        order_by="Milestone.rank",
        lazy="selectin"
    )

    currency = relationship(
        "Currency",
        back_populates="projects"
    )

    wallet = relationship(
        "Wallet", 
        uselist=False, 
        primaryjoin="Project.id == Wallet.project_id",
        lazy="selectin"
    )

    invites = relationship(
        "Invite", 
        uselist=True, 
        primaryjoin="Project.id == Invite.project_id",
        lazy="selectin"
    )

    creator = relationship(
        "User",
        primaryjoin="User.id == Project.created_by",
        foreign_keys="Project.created_by",
        lazy="selectin"
    )

    @property
    def progress(self) -> int:
        # CRITICAL CATCH: Ignore soft-deleted milestones!
        active_milestones = [m for m in self.milestones if m.deleted_at is None]
        
        if not active_milestones:
            return 0
            
        completed_count = sum(1 for m in active_milestones if m.status == 3) # 3 = completed
        
        return int((completed_count / len(active_milestones)) * 100)


def create_project(db: Session, currency_id: int, name: str, start_date: str, end_date: str, created_by: int, total_fee: float = 0.0, description: str = None, status: int = 1, commit: bool = False):
    project = Project(
        currency_id=currency_id,
        name=name,
        start_date=start_date,
        end_date=end_date,
        description=description,
        total_fee=total_fee,
        status=status,
        created_by=created_by,
        created_at=get_laravel_datetime(),
        updated_at=get_laravel_datetime()
    )
    db.add(project)
    if not commit:
        db.flush()
    else:
        db.commit()
        db.refresh(project)
    return project


def update_project(db: Session, id: int = 0, values: Dict = {}, commit: bool = False):
    values['updated_at'] = get_laravel_datetime()
    db.query(Project).filter_by(id=id).update(values)
    if not commit:
        db.flush()
    else:
        db.commit()
    return True


def delete_project(db: Session, id: int = 0, commit: bool = False):
    values = {
        'updated_at': get_laravel_datetime(),
        'deleted_at': get_laravel_datetime(),
    }
    db.query(Project).filter_by(id=id).update(values)
    if not commit:
        db.flush()
    else:
        db.commit()
    return True


def force_delete_project(db: Session, id: int = 0, commit: bool = False):
    db.query(Project).filter_by(id=id).delete()
    if not commit:
        db.flush()
    else:
        db.commit()
    return True


def get_single_project_by_id(db: Session, id: int = 0):
    from .users import User
    return db.query(Project).options(
        selectinload(Project.currency),
        selectinload(Project.wallet),
        selectinload(Project.milestones),
        selectinload(Project.creator).selectinload(User.profile),
        selectinload(Project.roles).selectinload(Role.role_users).selectinload(Role_User.user).selectinload(User.profile),
    ).filter_by(id=id).first()

def get_just_single_project_by_id(db: Session, id: int = 0):
    return db.query(Project).filter_by(id=id).first()

def get_projects(db: Session, filters: Dict = {}):
    from .users import User
    query = db.query(Project).options(
        selectinload(Project.currency),
        selectinload(Project.wallet),
        selectinload(Project.milestones),
        selectinload(Project.creator).selectinload(User.profile),
        selectinload(Project.roles).selectinload(Role.role_users).selectinload(Role_User.user).selectinload(User.profile),
    ).filter(Project.deleted_at == None)
    
    if 'created_by' in filters:
        query = query.filter_by(created_by=filters['created_by'])
        
    if 'currency_id' in filters:
        query = query.filter_by(currency_id=filters['currency_id'])
        
    if 'ids' in filters:
        query = query.filter(Project.id.in_(filters['ids']))
        
    if 'status' in filters:
        query = query.filter_by(status=filters['status'])
        
    if 'name' in filters:
        query = query.filter(Project.name.ilike(f"%{filters['name']}%"))
        
    return query.order_by(desc(Project.created_at))
