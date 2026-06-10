from typing import Dict, List
from sqlalchemy.orm import Session
from database.model import create_bank_account, update_bank_account, delete_bank_account, force_delete_bank_account, get_bank_accounts, get_single_bank_account_by_id, set_default_bank_account
from modules.utils.tools import process_schema_dictionary
from fastapi_pagination.ext.sqlalchemy import paginate

# def insert_new_bank_account(db: Session, )