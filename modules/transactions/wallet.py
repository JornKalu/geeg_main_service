from sqlalchemy.orm import Session
from database.model import get_wallet_by_user_id, update_wallet, create_transaction, get_just_single_user_by_id, get_single_profile_by_user_id
from modules.external.korapay import create_virtual_bank_account
from modules.utils.tools import generate_transaction_reference
from typing import Dict, Any

def process_wallet_to_wallet_transfer(db: Session, from_user_id: int, to_user_id: int, amount: float, narration: str = None):
    """
    Handles transferring funds from one user's wallet to another.
    """
    if amount <= 0:
        return {'status': False, 'message': 'Transfer amount must be greater than zero'}

    # 1. Retrieve wallets for both users
    sender_wallet = get_wallet_by_user_id(db, user_id=from_user_id)
    receiver_wallet = get_wallet_by_user_id(db, user_id=to_user_id)

    if not sender_wallet:
        return {'status': False, 'message': 'Sender wallet not found'}
    if not receiver_wallet:
        return {'status': False, 'message': 'Receiver wallet not found'}

    # 2. Basic validation: ensure same currency (standard for internal transfers)
    if sender_wallet.currency_id != receiver_wallet.currency_id:
        return {'status': False, 'message': 'Currency mismatch: both wallets must use the same currency'}

    # 3. Check sender balance
    if float(sender_wallet.balance) < float(amount):
        return {'status': False, 'message': 'Insufficient wallet balance'}

    # 4. Snapshots for audit trail
    from_prev_bal = float(sender_wallet.balance)
    from_new_bal = from_prev_bal - float(amount)
    to_prev_bal = float(receiver_wallet.balance)
    to_new_bal = to_prev_bal + float(amount)

    # 5. Perform updates
    update_wallet(db, id=sender_wallet.id, values={'balance': from_new_bal})
    update_wallet(db, id=receiver_wallet.id, values={'balance': to_new_bal})

    # 6. Generate a unique transaction reference
    reference = generate_transaction_reference(tran_type="wallet_transfer")

    # 7. Create the transaction record
    transaction_data = {
        'from_user_id': from_user_id,
        'to_user_id': to_user_id,
        'from_wallet_id': sender_wallet.id,
        'to_wallet_id': receiver_wallet.id,
        'narration': narration,
        'from_wallet_previous_balance': from_prev_bal,
        'from_wallet_new_balance': from_new_bal,
        'to_wallet_previous_balance': to_prev_bal,
        'to_wallet_new_balance': to_new_bal,
        'status': 'completed'
    }

    transaction = create_transaction(
        db=db,
        transaction_type='wallet_transfer',
        reference=reference,
        amount=amount,
        total_amount=amount, # Assuming zero fee for peer-to-peer internal transfers
        values=transaction_data,
        commit=False
    )

    return {
        'status': True,
        'message': 'Success',
        'data': transaction
    }

def generate_virtual_account_number(db: Session, user_id: int):
    user = get_just_single_user_by_id(db=db, id=user_id)
    if user is None:
        return {
            'status': False,
            'message': 'User not found',
            'data': None,
        }
    profile = get_single_profile_by_user_id(db=db, user_id=user_id)
    if profile is None:
        return {
            'status': False,
            'message': 'Profile not found',
            'data': None,
        }
    
    if profile.bvn is None or profile.bvn == "":
        return {
            'status': False,
            'message': 'Please add BVN',
            'data': None
        }
    
    user_wallet = get_wallet_by_user_id(db, user_id=user_id)
    if not user_wallet:
        return {'status': False, 'message': 'User wallet not found', 'data': None}
    
    if user_wallet.is_generated == 1:
        return {'status': False, 'message': 'Account already generated', 'data': None}

    bvn = profile.bvn
    nin = profile.nin

    full_name = f"{profile.first_name} {profile.last_name}"
    account_reference = f"USER_{user_id}_VA"

    customer = {
        "name": full_name,
        "email": user.email
    }
    kyc = {
        "bvn": bvn
    }
    if nin:
        kyc["nin"] = nin

    # 1. Call KoraPay API to create the virtual account
    response = create_virtual_bank_account(
        account_reference=account_reference,
        account_name=full_name,
        bank_code=None,  # KoraPay assigns this automatically if not provided
        customer=customer,
        kyc=kyc
    )

    if not response.get('status'):
        return {
            'status': False,
            'message': response.get('message', 'Failed to create virtual account'),
            'data': response.get('data')
        }

    va_data = response.get('data', {})

    # 2. Update the wallet record with the new virtual account details
    update_wallet(db, id=user_wallet.id, values={
        'account_name': va_data.get('account_name'),
        'account_number': va_data.get('account_number'),
        'bank_name': va_data.get('bank_name'),
        'bank_code': va_data.get('bank_code'),
        'external_reference': account_reference,
        'is_generated': 1
    })

    return {
        'status': True,
        'message': 'Success',
        'data': {
            'account_name': va_data.get('account_name'),
            'account_number': va_data.get('account_number'),
            'bank_name': va_data.get('bank_name')
        }
    }

    
    
    