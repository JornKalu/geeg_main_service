from typing import Dict, List
from sqlalchemy.orm import Session
from database.model import create_bank_account, update_bank_account, delete_bank_account, force_delete_bank_account, get_bank_accounts, get_single_bank_account_by_id, set_default_bank_account, get_just_single_bank_account_by_id
from modules.utils.tools import process_schema_dictionary
from fastapi_pagination.ext.sqlalchemy import paginate

def insert_new_bank_account(db: Session, user_id: int, account_name: str, account_number: str, bank_name: str, bank_code: str, is_default: bool = False):
    """
    Inserts a new bank account for a user.
    """
    bank_account = create_bank_account(db=db, user_id=user_id, account_name=account_name, account_number=account_number, bank_name=bank_name, bank_code=bank_code, is_default=is_default, status=1)
    return {
        'status': True,
        'message': 'Success',
        'data': bank_account
    }

def update_existing_bank_account(db: Session, id: int, user_id: int, values: Dict = {}):
    """
    Updates an existing bank account.
    """
    bank_account = get_just_single_bank_account_by_id(db=db, id=id)
    if bank_account is None:
        return {
            'status': False,
            'message': 'Bank account not found',
        }
    if bank_account.user_id != user_id:
        return {
            'status': False,
            'message': 'You are not authorized to update this bank account',
        }
    values = process_schema_dictionary(info=values)
    update_bank_account(db=db, id=id, values=values)
    return {
        'status': True,
        'message': 'Success',
    }

def delete_existing_bank_account(db: Session, id: int, user_id: int):
    """
    Deletes an existing bank account.
    """
    bank_account = get_just_single_bank_account_by_id(db=db, id=id)
    if bank_account is None:
        return {
            'status': False,
            'message': 'Bank account not found',
        }
    if bank_account.user_id != user_id:
        return {
            'status': False,
            'message': 'You are not authorized to delete this bank account',
        }
    delete_bank_account(db=db, id=id)
    return {
        'status': True,
        'message': 'Success',
    }

def retrieve_bank_accounts(db: Session, user_id: int, filters: Dict = {}):
    """
    Retrieves all bank accounts for a given user.
    """
    filters['user_id'] = user_id
    data = get_bank_accounts(db=db, filters=filters)
    return paginate(data)

def retrieve_single_bank_account(db: Session, id: int, user_id: int):
    """
    Retrieves a single bank account by its ID and ensures it belongs to the user.
    """
    bank_account = get_single_bank_account_by_id(db=db, id=id)
    if bank_account is None:
        return {
            'status': False,
            'message': 'Bank account not found',
            'data': None
        }
    if bank_account.user_id != user_id:
        return {
            'status': False,
            'message': 'You are not authorized to view this bank account',
            'data': None
        }
    return {
        'status': True,
        'message': 'Success',
        'data': bank_account
    }

def make_bank_account_default(db: Session, id: int, user_id: int):
    """
    Sets a specific bank account as the default for a user.
    """
    bank_account = get_just_single_bank_account_by_id(db=db, id=id)
    if bank_account is None:
        return {
            'status': False,
            'message': 'Bank account not found',
        }
    if bank_account.user_id != user_id:
        return {
            'status': False,
            'message': 'You are not authorized to set this bank account as default',
        }
    set_default_bank_account(db=db, user_id=user_id, bank_account_id=id)
    return {
        'status': True,
        'message': 'Default bank account set successfully',
    }