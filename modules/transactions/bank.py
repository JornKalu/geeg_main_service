from typing import Dict, List
from sqlalchemy.orm import Session
from database.model import create_bank_account, update_bank_account, delete_bank_account, force_delete_bank_account, get_bank_accounts, get_single_bank_account_by_id, set_default_bank_account, get_just_single_bank_account_by_id, get_wallet_by_user_id, update_wallet, create_transaction
from modules.utils.tools import process_schema_dictionary, generate_transaction_reference
from fastapi_pagination.ext.sqlalchemy import paginate
from modules.external.korapay import payout_bank_transfer

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

def process_external_bank_transfer(db: Session, user_id: int, bank_account_id: int, amount: float, narration: str = None):
    """
    Handles transferring funds from a user's wallet to an external bank account.
    """
    if amount <= 0:
        return {'status': False, 'message': 'Transfer amount must be greater than zero'}

    # 1. Retrieve and validate the chosen bank account
    bank_account = get_just_single_bank_account_by_id(db, id=bank_account_id)
    if not bank_account:
        return {'status': False, 'message': 'Bank account not found', 'data': None}
    
    if bank_account.user_id != user_id:
        return {'status': False, 'message': 'You are not authorized to use this bank account', 'data': None}

    # 2. Retrieve user wallet and check balance
    user_wallet = get_wallet_by_user_id(db, user_id=user_id)
    if not user_wallet:
        return {'status': False, 'message': 'User wallet not found', 'data': None}

    if float(user_wallet.balance) < float(amount):
        return {'status': False, 'message': 'Insufficient wallet balance', 'data': None}

    # 3. Generate transaction reference
    reference = generate_transaction_reference(tran_type="external_transfer")

    # 4. Debit the user's wallet
    prev_balance = float(user_wallet.balance)
    new_balance = prev_balance - float(amount)
    update_wallet(db, id=user_wallet.id, values={'balance': new_balance}, commit=False)

    # 5. Create the transaction record (initially pending)
    transaction_data = {
        'from_user_id': user_id,
        'from_wallet_id': user_wallet.id,
        'bank_account_id': bank_account_id,
        'provider': 'korapay',
        'narration': narration if narration else f"Withdrawal to {bank_account.bank_name} ({bank_account.account_number})",
        'from_wallet_previous_balance': prev_balance,
        'from_wallet_new_balance': new_balance,
        'status': 'pending',
        'external_account_name': bank_account.account_name,
        'external_account_number': bank_account.account_number,
        'external_bank_name': bank_account.bank_name
    }

    transaction = create_transaction(
        db=db,
        transaction_type='external_transfer',
        reference=reference,
        amount=amount,
        total_amount=amount, # Assuming zero fee for now
        values=transaction_data,
    )

    # 6. Call KoraPay Payout API
    payout_response = payout_bank_transfer(
        amount=amount,
        reference=reference,
        bank_code=bank_account.bank_code,
        account_number=bank_account.account_number,
        narration=narration
    )

    if not payout_response.get('status'):
        return {
            'status': False, 
            'message': payout_response.get('message', 'Failed to initiate external transfer'),
            'data': payout_response.get('data')
        }

    return {
        'status': True,
        'message': 'Success',
        'data': transaction
    }