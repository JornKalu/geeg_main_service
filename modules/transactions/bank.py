from typing import Dict, List
from decimal import Decimal
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from database.model import create_bank_account, update_bank_account, delete_bank_account, force_delete_bank_account, get_bank_accounts, get_single_bank_account_by_id, set_default_bank_account, get_just_single_bank_account_by_id, get_wallet_by_user_id, update_wallet, create_transaction, update_transaction, get_single_transaction_by_id
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
    # filters['user_id'] = user_id
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
    set_default_bank_account(db=db, user_id=user_id, account_id=id)
    return {
        'status': True,
        'message': 'Default bank account set successfully',
    }

def process_external_bank_transfer(
    db: Session, 
    user_id: int, 
    user_email: str,
    bank_account_id: int, 
    amount: float, 
    narration: str = None
):
    """
    Handles transferring funds from a user's wallet to an external bank account.
    Designed for FastAPI generators with auto-commit enabled.
    """
    transfer_amount = Decimal(str(amount))
    if transfer_amount <= Decimal('0.00'):
        return {'status': False, 'message': 'Transfer amount must be greater than zero'}

    bank_account = get_just_single_bank_account_by_id(db, id=bank_account_id)
    if not bank_account:
        return {'status': False, 'message': 'Bank account not found', 'data': None}
    
    if bank_account.user_id != user_id:
        return {'status': False, 'message': 'You are not authorized to use this bank account', 'data': None}

    # =================================================================
    # PHASE 1: THE ATOMIC STAGE (Flush to DB, do not commit yet)
    # =================================================================
    try:
        # 1. Grab the wallet and slap a FOR UPDATE SQL lock on it.
        locked_wallet = get_wallet_by_user_id(db=db, user_id=user_id, for_update=True)

        if not locked_wallet:
            return {'status': False, 'message': 'User wallet not found', 'data': None}

        current_balance = Decimal(str(locked_wallet.balance))
        if current_balance < transfer_amount:
            return {'status': False, 'message': 'Insufficient wallet balance', 'data': None}

        reference = generate_transaction_reference(tran_type="external_transfer")
        new_balance = current_balance - transfer_amount

        # 2. Stage the debit. Your helper calls db.flush() when commit=False.
        update_wallet(
            db=db, 
            id=locked_wallet.id, 
            values={'balance': new_balance}
        )

        transaction_data = {
            'from_user_id': user_id,
            'from_wallet_id': locked_wallet.id,
            'bank_account_id': bank_account_id,
            'provider': 'korapay',
            'narration': narration if narration else f"Withdrawal to {bank_account.bank_name} ({bank_account.account_number})",
            'from_wallet_previous_balance': current_balance,
            'from_wallet_new_balance': new_balance,
            'status': 0,
            'external_account_name': bank_account.account_name,
            'external_account_number': bank_account.account_number,
            'external_bank_name': bank_account.bank_name
        }

        # 3. Stage the transaction log. Your helper calls db.flush() when commit=False.
        transaction = create_transaction(
            db=db,
            transaction_type='external_transfer',
            reference=reference,
            amount=transfer_amount,
            total_amount=transfer_amount, 
            values=transaction_data
        )

    except SQLAlchemyError:
        # If staging fails, your FastAPI get_db() will catch the router exception 
        # and hit db.rollback() automatically.
        return {'status': False, 'message': 'Database error staging transaction.', 'data': None}

    # =================================================================
    # PHASE 2: THE NETWORK CALL (Row remains locked in memory)
    # =================================================================
    try:
        payout_response = payout_bank_transfer(
            amount=float(transfer_amount),
            reference=reference,
            bank_code=bank_account.bank_code,
            account_number=bank_account.account_number,
            customer_email=user_email,
            customer_name=bank_account.account_name,
            narration=narration or "Geeg Withdraw"
        )
    except Exception as net_err:
        # Gateway timed out. Return True. 
        # When this function ends, get_db() will commit the 'pending' transaction.
        return {
            'status': True,
            'message': 'Transfer initiated; awaiting gateway verification.',
            'data': transaction
        }

    # =================================================================
    # PHASE 3: RECONCILIATION
    # =================================================================
    if not payout_response.get('status'):
        # Instant rejection by KoraPay (e.g. Bank Account Blocked)
        # We undo our staged math right here in the open transaction session.
        refund_balance = Decimal(str(locked_wallet.balance)) + transfer_amount
        
        update_wallet(db, id=locked_wallet.id, values={'balance': refund_balance}, commit=False)
        update_transaction(
            db, 
            id=transaction.id, 
            values={'status': 2, 'meta_data': payout_response}
        )

        return {
            'status': False, 
            'message': payout_response.get('message', 'Transfer rejected by payment provider'),
            'data': payout_response.get('data')
        }

    # Kora accepted it into their queue!
    kora_data = payout_response.get('data', {})
    update_transaction(
        db,
        id=transaction.id,
        values={
            'external_reference': kora_data.get('reference'),
            'meta_data': payout_response
        }
    )

    return {
        'status': True,
        'message': 'Success',
        'data': get_single_transaction_by_id(db=db, id=transaction.id)
    }