from typing import Dict, Any
from sqlalchemy import Column, String, BigInteger, SmallInteger, Text, DateTime, desc
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from database.db import Base, get_laravel_datetime


class General_Setting(Base):
    __tablename__ = "general_settings"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    value = Column(Text, nullable=True)
    multi_value = Column(JSONB, nullable=True)
    status = Column(SmallInteger, default=1) # 1=active, 0=inactive/disabled
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


def create_general_setting(db: Session, name: str, value: str = None, multi_value: Any = None, status: int = 1, commit: bool = False):
    setting = General_Setting(
        name=name,
        value=value,
        multi_value=multi_value,
        status=status,
        created_at=get_laravel_datetime(),
        updated_at=get_laravel_datetime()
    )
    db.add(setting)
    if not commit:
        db.flush()
    else:
        db.commit()
        db.refresh(setting)
    return setting


def update_general_setting(db: Session, id: int = 0, values: Dict = {}, commit: bool = False):
    values['updated_at'] = get_laravel_datetime()
    db.query(General_Setting).filter_by(id=id).update(values)
    if not commit:
        db.flush()
    else:
        db.commit()
    return True


def delete_general_setting(db: Session, id: int = 0, commit: bool = False):
    """
    Note: Your schema doesn't have deleted_at for this table, 
    so this is a hard delete.
    """
    db.query(General_Setting).filter_by(id=id).delete()
    if not commit:
        db.flush()
    else:
        db.commit()
    return True


def get_single_setting_by_id(db: Session, id: int = 0):
    return db.query(General_Setting).filter_by(id=id).first()


def get_setting_by_name(db: Session, name: str):
    """
    Retrieves a setting by its unique name key.
    """
    return db.query(General_Setting).filter_by(name=name).first()


def get_setting_value(db: Session, name: str, default: Any = None):
    """
    A utility to quickly get the value or multi_value of a setting.
    """
    setting = db.query(General_Setting).filter_by(name=name, status=1).first()
    if not setting:
        return default
    return setting.multi_value if setting.multi_value is not None else setting.value


def get_general_settings(db: Session, filters: Dict = {}):
    query = db.query(General_Setting)
    
    if 'status' in filters:
        query = query.filter_by(status=filters['status'])
        
    if 'name' in filters:
        query = query.filter(General_Setting.name.ilike(f"%{filters['name']}%"))
        
    return query.order_by(General_Setting.name.asc())