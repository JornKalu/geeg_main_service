from typing import Dict, List
from sqlalchemy.orm import Session
from database.model import create_project
from modules.utils.tools import process_schema_dictionary
from fastapi_pagination.ext.sqlalchemy import paginate

# def insert_new_project(db: Session, )