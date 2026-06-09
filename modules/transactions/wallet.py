from sqlalchemy.orm import Session
from database.model import get_wallet_by_user_id, update_wallet, create_transaction
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
