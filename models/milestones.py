from typing import Dict
from sqlalchemy import Column, String, BigInteger, Integer, SmallInteger, Text, Date, TIMESTAMP, desc, asc
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from database.db import Base, get_laravel_datetime


class Milestone(Base):
    __tablename__ = "milestones"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    project_id = Column(BigInteger, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    rank = Column(Integer, default=0) # For ordering milestones within a project
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    status = Column(SmallInteger, default=1) # 1=pending, 2=in_progress, 3=completed, 4=delayed, 5=cancelled
    assigned_to = Column(BigInteger, nullable=True)
    created_by = Column(BigInteger, nullable=False)
    created_at = Column(TIMESTAMP, nullable=True, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=True, server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP, nullable=True)


def create_milestone(db: Session, project_id: int, name: str, created_by: int, description: str = None, rank: int = 0, start_date: any = None, end_date: any = None, status: int = 1, assigned_to: int = None, commit: bool = False):
    milestone = Milestone(
        project_id=project_id,
        name=name,
        description=description,
        rank=rank,
        start_date=start_date,
        end_date=end_date,
        status=status,
        assigned_to=assigned_to,
        created_by=created_by,
        created_at=get_laravel_datetime(),
        updated_at=get_laravel_datetime()
    )
    db.add(milestone)
    if not commit:
        db.flush()
    else:
        db.commit()
        db.refresh(milestone)
    return milestone


def update_milestone(db: Session, id: int = 0, values: Dict = {}, commit: bool = False):
    values['updated_at'] = get_laravel_datetime()
    db.query(Milestone).filter_by(id=id).update(values)
    if not commit:
        db.flush()
    else:
        db.commit()
    return True


def delete_milestone(db: Session, id: int = 0, commit: bool = False):
    values = {
        'updated_at': get_laravel_datetime(),
        'deleted_at': get_laravel_datetime(),
    }
    db.query(Milestone).filter_by(id=id).update(values)
    if not commit:
        db.flush()
    else:
        db.commit()
    return True


def force_delete_milestone(db: Session, id: int = 0, commit: bool = False):
    db.query(Milestone).filter_by(id=id).delete()
    if not commit:
        db.flush()
    else:
        db.commit()
    return True


def get_single_milestone_by_id(db: Session, id: int = 0):
    return db.query(Milestone).filter_by(id=id).first()


def get_project_milestones(db: Session, project_id: int):
    """
    Fetches all active milestones for a specific project, ordered by their rank.
    Perfect for rendering project roadmaps or sequential tasks.
    """
    return db.query(Milestone).filter_by(
        project_id=project_id, 
        deleted_at=None
    ).order_by(asc(Milestone.rank), asc(Milestone.start_date)).all()


def get_milestones(db: Session, filters: Dict = {}):
    query = db.query(Milestone).filter(Milestone.deleted_at == None)
    
    if 'project_id' in filters:
        query = query.filter_by(project_id=filters['project_id'])
        
    if 'status' in filters:
        query = query.filter_by(status=filters['status'])
        
    if 'assigned_to' in filters:
        query = query.filter_by(assigned_to=filters['assigned_to'])
        
    if 'created_by' in filters:
        query = query.filter_by(created_by=filters['created_by'])
        
    if 'name' in filters:
        query = query.filter(Milestone.name.ilike(f"%{filters['name']}%"))
        
    return query.order_by(desc(Milestone.created_at))