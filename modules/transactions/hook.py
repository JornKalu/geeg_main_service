from typing import Dict, Any
import hmac
import hashlib
import json
import traceback

from sqlalchemy.orm import Session

from settings.config import load_env_config

from database.model import create_transaction, get_transaction_by_reference, update_wallet, get_wallet_by_user_id, get_wallet_by_account_number
from modules.utils.tools import generate_transaction_reference
from modules.messaging.email import e_notification

config = load_env_config()

def verify_korapay_signature(body: bytes, headers: Dict) -> bool:
    """
    Verifies the authenticity of the KoraPay webhook request using the signature.
    """
    korapay_signature = headers.get("x-korapay-signature")
    if not korapay_signature:
        print("KoraPay signature header missing.")
        return False

    secret_key = config['korapay_secret_key'].encode('utf-8')
    computed_signature = hmac.new(secret_key, body, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(korapay_signature, computed_signature):
        print(f"Signature mismatch. Received: {korapay_signature}, Computed: {computed_signature}")
        return False
    
    print("KoraPay signature verified successfully.")
    return True

def process_korapay_event(db: Session, payload: Dict) -> Dict:
    """
    Processes the incoming KoraPay webhook event and dispatches to appropriate handlers.
    """
    event_type = payload.get("event")
    data = payload.get("data")

    if not event_type or not data:
        print(f"Invalid KoraPay event structure: {payload}")
        return {"status": "error", "message": "Invalid KoraPay event structure"}

    print(f"Processing KoraPay event: {event_type}")

    if event_type == "virtual_account.payment_successful":
        return handle_virtual_account_payment(db, data)
    elif event_type == "transaction.successful":
        # Check if this general transaction success is specifically for a virtual account deposit
        if data.get("type") == "deposit" and data.get("channel") == "virtual_account":
             return handle_virtual_account_payment(db, data)
        else:
            print(f"Unhandled transaction.successful event type or channel: {data.get('type')}, {data.get('channel')}")
            return {"status": "success", "message": "Event received but not processed for this type."}
    else:
        print(f"Unhandled KoraPay event type: {event_type}")
        return {"status": "success", "message": "Event received but not processed."}

def handle_virtual_account_payment(db: Session, payment_data: Dict) -> Dict:
    """
    Handles the logic for a successful virtual account payment.
    Updates wallet balance, creates a transaction record, and sends notifications.
    """
    try:
        amount = float(payment_data.get("amount"))
        currency = payment_data.get("currency")
        korapay_reference = payment_data.get("reference")
        narration = payment_data.get("description", "Virtual account deposit")
        customer_info = payment_data.get("customer", {})
        virtual_bank_account_details = payment_data.get("virtual_bank_account_details", {})
        
        # Idempotency check: Prevent reprocessing the same webhook
        existing_transaction = get_transaction_by_reference(db, reference=korapay_reference)
        if existing_transaction and existing_transaction.status == 'completed':
            print(f"Duplicate webhook for KoraPay reference {korapay_reference}. Already processed.")
            return {"status": "success", "message": "Duplicate event, already processed."}
        

        
        # Extract user_id from account_reference.
        # Assuming account_reference is in the format "USER_{user_id}_VA"
        account_reference = None
        account_name = None
        account_number = None
        bank_name = None

        if virtual_bank_account_details != {}:
            payer_bank_account = virtual_bank_account_details.get("payer_bank_account", {})

            if payer_bank_account != {}:
                account_name = payer_bank_account.get('account_name', None)
                account_number = payer_bank_account.get('account_number', None)
                bank_name = payer_bank_account.get('bank_name', None)
            
            virtual_bank_account = virtual_bank_account_details.get("virtual_bank_account", {})

            if virtual_bank_account != {}:
                account_reference = virtual_bank_account.get("account_reference", "")
        

        # account_reference = payment_data.get("account_reference", "")
        account_reference_parts = account_reference.split('_')
        if len(account_reference_parts) < 2 or not account_reference_parts[1].isdigit():
            error_msg = f"Could not parse user_id from account_reference: {account_reference}"
            print(error_msg)
            e_notification(
                email=config.get('admin_email', 'admin@example.com'),
                title="KoraPay Webhook Error",
                sub_title=f"Failed to process virtual account payment: Invalid account reference",
                recipient_name="Admin",
                msg=f"{error_msg}. Payload: {payment_data}"
            )
            return {"status": "error", "message": error_msg}
            
        user_id = int(account_reference_parts[1])

        user_wallet = get_wallet_by_user_id(db, user_id=user_id)
        if not user_wallet:
            error_msg = f"Wallet not found for user_id: {user_id} for KoraPay reference {korapay_reference}"
            print(error_msg)
            e_notification(
                email=config.get('admin_email', 'admin@example.com'),
                title="KoraPay Webhook Error",
                sub_title=f"Wallet not found for user {user_id}",
                recipient_name="Admin",
                msg=f"{error_msg}. Payload: {payment_data}"
            )
            return {"status": "error", "message": "User wallet not found"}

        prev_balance = float(user_wallet.balance)
        new_balance = prev_balance + amount
        update_wallet(db, id=user_wallet.id, values={'balance': new_balance}, commit=False)


        internal_reference = generate_transaction_reference(tran_type="deposit")
        transaction_data = {
            'to_user_id': user_id,
            'to_wallet_id': user_wallet.id,
            'narration': narration,
            'from_wallet_previous_balance': prev_balance, # For deposits, from_wallet is not applicable, but we can use this for audit
            'from_wallet_new_balance': new_balance,
            'to_wallet_previous_balance': prev_balance,
            'to_wallet_new_balance': new_balance,
            'status': 'completed',
            'provider': 'korapay',
            'external_reference': korapay_reference,
            'external_account_name': account_name,
            'external_account_number': account_number,
            'external_bank_name': bank_name,
            'meta_data': payment_data
        }
        create_transaction(db=db, transaction_type='deposit', reference=internal_reference, amount=amount, total_amount=amount, values=transaction_data, commit=True)

        user_email = customer_info.get("email")
        user_name = customer_info.get("name", f"User {user_id}")
        if user_email:
            e_notification(
                email=user_email,
                title="Deposit Successful",
                sub_title=f"Your account has been credited with {currency} {amount:,.2f}",
                recipient_name=user_name,
                msg=f"A deposit of {currency} {amount:,.2f} has been successfully credited to your wallet. Your new balance is {currency} {new_balance:,.2f}. Transaction Reference: {internal_reference}"
            )

        print(f"Successfully processed virtual account payment for user {user_id}, reference {korapay_reference}")
        return {"status": "success", "message": "Virtual account payment processed successfully"}

    except Exception as e:
        db.rollback() # Rollback any changes if an error occurs
        error_trace = traceback.format_exc()
        print(f"Error processing KoraPay virtual account payment: {e}\n{error_trace}")
        e_notification(
            email=config.get('admin_email', 'admin@example.com'),
            title="KoraPay Webhook Critical Error",
            sub_title=f"Failed to process virtual account payment: {e}",
            recipient_name="Admin",
            msg=f"A critical error occurred while processing a KoraPay virtual account payment. Reference: {payment_data.get('reference')}. Error: {e}. Full payload: {payment_data}. Stack Trace: {error_trace}"
        )
        return {"status": "error", "message": "Internal server error during payment processing."}