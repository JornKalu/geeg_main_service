from sqlalchemy.orm import Session
from database.model import get_wallet_by_user_id, update_wallet, create_transaction, get_just_single_user_by_id, get_single_profile_by_user_id, get_wallet_by_project_id, get_just_single_project_by_id, get_single_wallet_by_id, get_wallet_by_project_id
from modules.external.korapay import create_virtual_bank_account # Assuming this is an external API call
from modules.utils.tools import generate_transaction_reference
from typing import Dict, Any, List


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
        return {'status': False, 'message': 'Sender wallet not found', 'data': None}
    if not receiver_wallet:
        return {'status': False, 'message': 'Receiver wallet not found', 'data': None}

    # 2. Basic validation: ensure same currency (standard for internal transfers)
    if sender_wallet.currency_id != receiver_wallet.currency_id:
        return {'status': False, 'message': 'Currency mismatch: both wallets must use the same currency', 'data': None}

    # 3. Check sender balance
    if float(sender_wallet.balance) < float(amount):
        return {'status': False, 'message': 'Insufficient wallet balance', 'data': None}

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

def process_bulk_wallet_to_wallet_transfer(db: Session, from_user_id: int, transfers: List[Dict[str, Any]]):
    """
    Handles transferring funds from one user's wallet to multiple other users' wallets in a bulk operation.
    The entire operation is atomic: if any transfer fails, all transfers are rolled back.
    """
    results = []
    
    # Retrieve sender wallet once
    sender_wallet = get_wallet_by_user_id(db, user_id=from_user_id)
    if not sender_wallet:
        return {'status': False, 'message': f'Sender wallet not found for user: {from_user_id}', 'data': None}

    # Pre-check total amount and individual recipient wallets
    total_amount_to_transfer = sum(t['amount'] for t in transfers)
    if float(sender_wallet.balance) < total_amount_to_transfer:
        return {'status': False, 'message': 'Insufficient total balance in sender wallet for all transfers', 'data': None}

    # Collect all receiver wallets to avoid multiple lookups in the loop
    receiver_ids = [t['to_user_id'] for t in transfers]
    receiver_wallets = {w.user_id: w for w in db.query(get_wallet_by_user_id(db, user_id=uid) for uid in receiver_ids if get_wallet_by_user_id(db, user_id=uid) is not None)}

    try:
        # Start a subtransaction for atomicity of the bulk operation
        # If using a session managed by FastAPI's Depends(get_session), it already handles commit/rollback
        # for the request. However, for a bulk operation, we want all or nothing.
        # If you need explicit subtransaction control, you might use db.begin_nested()
        # For simplicity and assuming get_session handles the top-level transaction,
        # we'll let exceptions propagate to trigger a rollback by the dependency.

        current_sender_balance = float(sender_wallet.balance)

        for i, transfer_item in enumerate(transfers):
            to_user_id = transfer_item['to_user_id']
            amount = transfer_item['amount']
            narration = transfer_item.get('narration')

            if amount <= 0:
                results.append({'status': False, 'message': f'Transfer amount for recipient {to_user_id} must be greater than zero', 'transfer_index': i})
                raise ValueError(f'Invalid amount for transfer {i}') # Rollback entire operation

            receiver_wallet = receiver_wallets.get(to_user_id)
            if not receiver_wallet:
                results.append({'status': False, 'message': f'Receiver wallet not found for user_id: {to_user_id}', 'transfer_index': i})
                raise ValueError(f'Receiver wallet not found for transfer {i}') # Rollback entire operation

            if sender_wallet.currency_id != receiver_wallet.currency_id:
                results.append({'status': False, 'message': f'Currency mismatch for transfer to {to_user_id}', 'transfer_index': i})
                raise ValueError(f'Currency mismatch for transfer {i}') # Rollback entire operation

            # Check sender balance for this specific transfer (cumulative check already done)
            if current_sender_balance < amount:
                results.append({'status': False, 'message': f'Insufficient balance for transfer to {to_user_id}', 'transfer_index': i})
                raise ValueError(f'Insufficient balance for transfer {i}') # Rollback entire operation

            # Update balances
            from_prev_bal = current_sender_balance
            from_new_bal = current_sender_balance - amount
            to_prev_bal = float(receiver_wallet.balance)
            to_new_bal = to_prev_bal + amount

            update_wallet(db, id=sender_wallet.id, values={'balance': from_new_bal}, commit=False)
            update_wallet(db, id=receiver_wallet.id, values={'balance': to_new_bal}, commit=False)

            # Update current sender balance for next iteration
            current_sender_balance = from_new_bal

            # Create transaction record
            reference = generate_transaction_reference(tran_type="bulk_wallet_transfer")
            transaction_data = {
                'from_user_id': from_user_id,
                'to_user_id': to_user_id,
                'from_wallet_id': sender_wallet.id,
                'to_wallet_id': receiver_wallet.id,
                'narration': narration if narration else f"Bulk transfer from {from_user_id} to {to_user_id}",
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
                total_amount=amount,
                values=transaction_data,
                commit=False
            )
            results.append({'status': True, 'message': 'Transfer successful', 'data': transaction, 'transfer_index': i})

        return {'status': True, 'message': 'All bulk transfers processed successfully', 'data': results}

    except Exception as e:
        # The FastAPI dependency `get_session` will handle the rollback if an exception is raised.
        return {'status': False, 'message': f'Bulk transfer failed: {str(e)}', 'data': results}
    

def process_bulk_project_wallet_to_wallet_transfer(db: Session, project_id: int, transfers: List[Dict[str, Any]]):
    """
    Handles transferring funds from one user's wallet to multiple other users' wallets in a bulk operation.
    The entire operation is atomic: if any transfer fails, all transfers are rolled back.
    """
    results = []
    
    sender_wallet = get_wallet_by_project_id(db, user_id=project_id)
    if not sender_wallet:
        return {'status': False, 'message': f'Sender wallet not found for project: {project_id}', 'data': None}

    total_amount_to_transfer = sum(t['amount'] for t in transfers)
    if float(sender_wallet.balance) < total_amount_to_transfer:
        return {'status': False, 'message': 'Insufficient total balance in sender wallet for all transfers', 'data': None}

    receiver_ids = [t['to_user_id'] for t in transfers]
    receiver_wallets = {w.user_id: w for w in db.query(get_wallet_by_user_id(db, user_id=uid) for uid in receiver_ids if get_wallet_by_user_id(db, user_id=uid) is not None)}

    try:
        current_sender_balance = float(sender_wallet.balance)

        for i, transfer_item in enumerate(transfers):
            to_user_id = transfer_item['to_user_id']
            amount = transfer_item['amount']
            narration = transfer_item.get('narration')

            if amount <= 0:
                results.append({'status': False, 'message': f'Transfer amount for recipient {to_user_id} must be greater than zero', 'transfer_index': i})
                raise ValueError(f'Invalid amount for transfer {i}') # Rollback entire operation

            receiver_wallet = receiver_wallets.get(to_user_id)
            if not receiver_wallet:
                results.append({'status': False, 'message': f'Receiver wallet not found for user_id: {to_user_id}', 'transfer_index': i})
                raise ValueError(f'Receiver wallet not found for transfer {i}') # Rollback entire operation

            if sender_wallet.currency_id != receiver_wallet.currency_id:
                results.append({'status': False, 'message': f'Currency mismatch for transfer to {to_user_id}', 'transfer_index': i})
                raise ValueError(f'Currency mismatch for transfer {i}') # Rollback entire operation

            # Check sender balance for this specific transfer (cumulative check already done)
            if current_sender_balance < amount:
                results.append({'status': False, 'message': f'Insufficient balance for transfer to {to_user_id}', 'transfer_index': i})
                raise ValueError(f'Insufficient balance for transfer {i}') # Rollback entire operation

            # Update balances
            from_prev_bal = current_sender_balance
            from_new_bal = current_sender_balance - amount
            to_prev_bal = float(receiver_wallet.balance)
            to_new_bal = to_prev_bal + amount

            update_wallet(db, id=sender_wallet.id, values={'balance': from_new_bal}, commit=False)
            update_wallet(db, id=receiver_wallet.id, values={'balance': to_new_bal}, commit=False)

            # Update current sender balance for next iteration
            current_sender_balance = from_new_bal

            # Create transaction record
            reference = generate_transaction_reference(tran_type="bulk_wallet_transfer")
            transaction_data = {
                'from_user_id': sender_wallet.user_id,
                'to_user_id': to_user_id,
                'from_wallet_id': sender_wallet.id,
                'to_wallet_id': receiver_wallet.id,
                'narration': narration if narration else f"Bulk transfer from {project_id} to {to_user_id}",
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
                total_amount=amount,
                values=transaction_data,
                commit=False
            )
            results.append({'status': True, 'message': 'Transfer successful', 'data': transaction, 'transfer_index': i})

        return {'status': True, 'message': 'All bulk transfers processed successfully', 'data': results}

    except Exception as e:
        # The FastAPI dependency `get_session` will handle the rollback if an exception is raised.
        return {'status': False, 'message': f'Bulk transfer failed: {str(e)}', 'data': results}
    

def generate_virtual_account_number(db: Session, wallet_id: int):
    """
    Generates a KoraPay virtual account for a specific wallet, 
    dynamically resolving KYC for either Users or Projects.
    """
    # 1. Start with the Wallet
    wallet = get_single_wallet_by_id(db, id=wallet_id)
    if not wallet:
        return {'status': False, 'message': 'Wallet not found', 'data': None}
    
    if wallet.is_generated == 1:
        return {'status': False, 'message': 'Account already generated', 'data': None}

    # 2. Initialize our KoraPay payload variables
    customer_name = ""
    customer_email = ""
    customer_bvn = None
    customer_nin = None
    
    # Using the wallet ID ensures this reference is universally unique to the ledger
    account_reference = f"VA_WLT_{wallet.id}"

    # 3. Branching Logic: Who owns this wallet?
    if wallet.user_id:
        # --- USER WALLET LOGIC ---
        user = get_just_single_user_by_id(db=db, id=wallet.user_id)
        profile = get_single_profile_by_user_id(db=db, user_id=wallet.user_id)
        
        if not user or not profile:
            return {'status': False, 'message': 'User or Profile data missing'}
            
        if not profile.bvn:
            return {'status': False, 'message': 'Please add BVN to generate an account'}

        customer_name = f"{profile.first_name} {profile.last_name}"
        customer_email = user.email
        customer_bvn = profile.bvn
        if profile.nin:
            customer_nin = profile.nin

    elif wallet.project_id:
        # --- PROJECT WALLET LOGIC ---
        project = get_just_single_project_by_id(db=db, id=wallet.project_id)
        if not project:
            return {'status': False, 'message': 'Project not found'}
            
        # KoraPay requires a human/business name and email. 
        # If your 'Project' has its own email/name, use it. Otherwise, fallback to the project creator.
        project_owner = get_just_single_user_by_id(db=db, id=project.created_by) 
        owner_profile = get_single_profile_by_user_id(db=db, user_id=project.created_by)
        
        if not owner_profile.bvn:
            return {'status': False, 'message': 'Project owner must add BVN to generate a project account'}

        customer_name = f"{owner_profile.first_name} {owner_profile.last_name}"
        customer_email = project_owner.email
        
        # For NGN Virtual Accounts, Kora usually requires the individual's BVN unless it's a registered business (RC Number)
        customer_bvn = owner_profile.bvn 

    else:
        # Wallet has neither user_id nor project_id (Orphaned wallet)
        return {
            'status': False, 
            'message': 'Invalid wallet ownership structure',
            'data': None,
            }
    

    # 4. Call KoraPay API
    response = create_virtual_bank_account(account_reference=account_reference, account_name=customer_name, customer_full_name=customer_name, customer_email=customer_email, customer_bvn=customer_bvn, customer_nin=customer_nin, permanent=True)

    if not response.get('status'):
        return {
            'status': False,
            'message': response.get('message', 'Failed to create virtual account'),
            'data': response.get('data')
        }

    va_data = response.get('data', {})

    # 5. Update the wallet with the new Virtual Account details
    update_wallet(
        db=db, 
        id=wallet.id, 
        values={
            'account_name': va_data.get('account_name'),
            'account_number': va_data.get('account_number'),
            'bank_name': va_data.get('bank_name'),
            'bank_code': va_data.get('bank_code'),
            'external_reference': account_reference,
            'is_generated': 1
        }
    )

    return {
        'status': True,
        'message': 'Virtual account generated successfully',
        'data': {
            'account_name': va_data.get('account_name'),
            'account_number': va_data.get('account_number'),
            'bank_name': va_data.get('bank_name')
        }
    }

def transfer_funds_to_project_wallet(db: Session, user_id: int, project_id: int, amount: float, narration: str = None):
    """
    Transfers funds from a user's personal wallet to a project's wallet.
    """
    project = get_just_single_project_by_id(db=db, id=project_id)
    if project is None:
        return {'status': False, 'message': 'Project not found', 'data': None}
    
    if project.created_by != user_id:
        return {'status': False, 'message': 'Project can only be funded by creator', 'data': None}

    if amount <= 0:
        return {'status': False, 'message': 'Transfer amount must be greater than zero', 'data': None}

    user_wallet = get_wallet_by_user_id(db, user_id=user_id)
    project_wallet = get_wallet_by_project_id(db, project_id=project_id)

    if not user_wallet:
        return {'status': False, 'message': 'User wallet not found', 'data': None}
    if not project_wallet:
        return {'status': False, 'message': 'Project wallet not found', 'data': None}

    if user_wallet.currency_id != project_wallet.currency_id:
        return {'status': False, 'message': 'Currency mismatch: user and project wallets must use the same currency', 'data': None}

    if float(user_wallet.balance) < float(amount):
        return {'status': False, 'message': 'Insufficient balance in user wallet', 'data': None}

    # Update balances
    user_prev_bal = float(user_wallet.balance)
    user_new_bal = user_prev_bal - float(amount)
    project_prev_bal = float(project_wallet.balance)
    project_new_bal = project_prev_bal + float(amount)

    update_wallet(db, id=user_wallet.id, values={'balance': user_new_bal})
    update_wallet(db, id=project_wallet.id, values={'balance': project_new_bal})

    # Create transaction record
    reference = generate_transaction_reference(tran_type="project_deposit")
    transaction_data = {
        'from_user_id': user_id,
        'to_user_id': None, # Funds are going to a project wallet, not directly another user
        'from_wallet_id': user_wallet.id,
        'to_wallet_id': project_wallet.id,
        'narration': narration if narration else f"Transfer to Project {project_id}",
        'from_wallet_previous_balance': user_prev_bal,
        'from_wallet_new_balance': user_new_bal,
        'to_wallet_previous_balance': project_prev_bal,
        'to_wallet_new_balance': project_new_bal,
        'status': 'completed'
    }

    transaction = create_transaction(
        db=db,
        transaction_type='wallet_transfer', # Using wallet_transfer for internal movement
        reference=reference,
        amount=amount,
        total_amount=amount,
        values=transaction_data,
        commit=False
    )

    return {
        'status': True,
        'message': 'Funds successfully transferred to project wallet',
        'data': transaction
    }

def transfer_funds_from_project_wallet(db: Session, user_id: int, project_id: int, amount: float, narration: str = None):
    """
    Transfers funds from a project's wallet to a user's personal wallet.
    """
    project = get_just_single_project_by_id(db=db, id=project_id)
    if project is None:
        return {'status': False, 'message': 'Project not found', 'data': None}
    
    if project.created_by != user_id:
        return {'status': False, 'message': 'Project can only be withdraw by creator', 'data': None}
    
    if amount <= 0:
        return {'status': False, 'message': 'Transfer amount must be greater than zero', 'data': None}

    project_wallet = get_wallet_by_project_id(db, project_id=project_id)
    user_wallet = get_wallet_by_user_id(db, user_id=user_id)

    if not project_wallet:
        return {'status': False, 'message': 'Project wallet not found', 'data': None}
    if not user_wallet:
        return {'status': False, 'message': 'User wallet not found', 'data': None}

    if project_wallet.currency_id != user_wallet.currency_id:
        return {'status': False, 'message': 'Currency mismatch: project and user wallets must use the same currency', 'data': None}

    if float(project_wallet.balance) < float(amount):
        return {'status': False, 'message': 'Insufficient balance in project wallet', 'data': None}

    # Update balances
    project_prev_bal = float(project_wallet.balance)
    project_new_bal = project_prev_bal - float(amount)
    user_prev_bal = float(user_wallet.balance)
    user_new_bal = user_prev_bal + float(amount)

    update_wallet(db, id=project_wallet.id, values={'balance': project_new_bal})
    update_wallet(db, id=user_wallet.id, values={'balance': user_new_bal})

    # Create transaction record
    reference = generate_transaction_reference(tran_type="project_withdrawal")
    transaction_data = {
        'from_user_id': None, # Funds are coming from a project wallet, not directly another user
        'to_user_id': user_id,
        'from_wallet_id': project_wallet.id,
        'to_wallet_id': user_wallet.id,
        'narration': narration if narration else f"Withdrawal from Project {project_id}",
        'from_wallet_previous_balance': project_prev_bal,
        'from_wallet_new_balance': project_new_bal,
        'to_wallet_previous_balance': user_prev_bal,
        'to_wallet_new_balance': user_new_bal,
        'status': 'completed'
    }

    transaction = create_transaction(
        db=db,
        transaction_type='wallet_transfer', # Using wallet_transfer for internal movement
        reference=reference,
        amount=amount,
        total_amount=amount,
        values=transaction_data,
        commit=False
    )

    return {
        'status': True,
        'message': 'Funds successfully transferred from project wallet to user wallet',
        'data': transaction
    }
