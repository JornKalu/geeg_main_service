from typing import Dict, Any
import hmac
import hashlib
import traceback
from decimal import Decimal
from sqlalchemy.orm import Session

from settings.config import load_env_config
from database.model import (
    Transaction, 
    create_transaction, 
    get_transaction_by_reference,
    get_transaction_by_external_reference, 
    update_wallet, 
    get_single_wallet_by_id, 
    update_transaction, 
    get_just_single_user_by_id
)
from modules.utils.tools import generate_transaction_reference
from modules.messaging.email import e_notification

config = load_env_config()

def verify_korapay_signature(body: bytes, headers: Dict) -> bool:
    """
    Verifies the authenticity of the KoraPay webhook request using HMAC SHA256.
    """
    korapay_signature = headers.get("x-korapay-signature")
    if not korapay_signature:
        print("KoraPay signature header missing.")
        return False

    secret_key = config['korapay_secret_key'].encode('utf-8')
    computed_signature = hmac.new(secret_key, body, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(korapay_signature, computed_signature):
        print("Signature mismatch. Webhook rejected.")
        return False
    
    return True


def process_korapay_event(db: Session, payload: Dict) -> Dict:
    """
    The KoraPay 'Mailroom'. Dispatches events to their specific handlers based on the official docs.
    """
    event_type = payload.get("event")
    data = payload.get("data")

    if not event_type or not data:
        return {"status": "error", "message": "Invalid KoraPay event structure"}

    print(f"Processing KoraPay event: {event_type}")

    # SCENARIO 1: INBOUND DEPOSITS (Virtual Accounts, Cards, etc.)
    if event_type == "charge.success":
        # Check if this charge specifically contains Virtual Account details
        if "virtual_bank_account_details" in data:
            return handle_virtual_account_payment(db, data)
        else:
            print("Received a standard card/web charge webhook. Implement specific handler if needed.")
            return {"status": "success", "message": "Standard charge received."}
             
    # SCENARIO 2: OUTBOUND TRANSFERS (Withdrawals)
    elif event_type in ["transfer.success", "transfer.failed"]:
        return handle_outbound_transfer_webhook(db, event_type, data)

    else:
        print(f"Unhandled KoraPay event type: {event_type}")
        return {"status": "success", "message": "Event received but not processed."}


def handle_virtual_account_payment(db: Session, payment_data: Dict) -> Dict:
    """
    Processes an INBOUND deposit to a Virtual Account from a 'charge.success' event.
    """
    try:
        amount = Decimal(str(payment_data.get("amount", 0)))
        currency = payment_data.get("currency")
        korapay_reference = payment_data.get("reference")
        narration = payment_data.get("description", "Virtual account deposit")
        customer_info = payment_data.get("customer", {})
        virtual_bank_account_details = payment_data.get("virtual_bank_account_details", {})
        
        # 1. FIX: Idempotency check using external_reference!
        # Because Kora auto-generated this reference (e.g. KPY-PAY-xyz), we query external_reference
        existing_transaction = db.query(Transaction).filter_by(
            external_reference=korapay_reference, 
            deleted_at=None
        ).first()
        
        if existing_transaction:
            print(f"Duplicate deposit webhook for Kora ref {korapay_reference}.")
            return {"status": "success", "message": "Duplicate event, already processed."}
        
        # 2. Extract Sender Details
        account_name = None
        account_number = None
        bank_name = None
        account_reference = ""

        payer = virtual_bank_account_details.get("payer_bank_account", {})
        if payer:
            account_name = payer.get('account_name')
            account_number = payer.get('account_number')
            bank_name = payer.get('bank_name')
        
        va = virtual_bank_account_details.get("virtual_bank_account", {})
        if va:
            account_reference = va.get("account_reference", "")
        
        # 3. Parse Wallet ID (Expecting format: VA_WLT_123)
        account_reference_parts = account_reference.split('_')
        if len(account_reference_parts) != 3 or account_reference_parts[0] != "VA" or not account_reference_parts[2].isdigit():
            return {"status": "error", "message": "Could not parse wallet_id"}
            
        wallet_id = int(account_reference_parts[2])

        # 4. Atomic Ledger Update
        locked_wallet = get_single_wallet_by_id(db=db, id=wallet_id, for_update=True)
        if not locked_wallet:
            return {"status": "error", "message": "Target wallet not found"}

        prev_balance = Decimal(str(locked_wallet.balance))
        new_balance = prev_balance + amount

        update_wallet(db, id=locked_wallet.id, values={'balance': new_balance}, commit=False)

        internal_reference = generate_transaction_reference(tran_type="deposit")
        transaction_data = {
            'to_user_id': locked_wallet.user_id,
            'to_wallet_id': locked_wallet.id,
            'narration': narration,
            'to_wallet_previous_balance': prev_balance,
            'to_wallet_new_balance': new_balance,
            'status': 1, # 1 = completed
            'provider': 'korapay',
            'external_reference': korapay_reference,
            'external_account_name': account_name,
            'external_account_number': account_number,
            'external_bank_name': bank_name,
            'meta_data': payment_data
        }
        
        create_transaction(
            db=db, 
            transaction_type='deposit', 
            reference=internal_reference, 
            amount=amount, 
            total_amount=amount, 
            values=transaction_data, 
            commit=True # We commit here to finalize the deposit immediately
        )

        # 5. Notify User
        user_email = customer_info.get("email")
        if user_email:
            e_notification(
                email=user_email,
                title="Deposit Successful",
                sub_title=f"Your account was credited with {currency} {amount:,.2f}",
                recipient_name=customer_info.get("name", "Valued Customer"),
                msg=f"A deposit of {currency} {amount:,.2f} has been successfully credited. New balance: {currency} {new_balance:,.2f}."
            )

        return {"status": "success", "message": "Virtual account payment processed successfully"}

    except Exception as e:
        db.rollback() 
        print(f"Error processing VA payment: {e}\n{traceback.format_exc()}")
        return {"status": "error", "message": "Internal server error."}


def handle_outbound_transfer_webhook(db: Session, event_type: str, payment_data: Dict) -> Dict:
    """
    Processes OUTBOUND withdrawals from the platform to a user's bank.
    Handles 'transfer.success' and 'transfer.failed' events.
    """
    try:
        # For payouts, Kora echoes back OUR internal reference that we generated!
        internal_reference = payment_data.get("reference")
        
        transaction = get_transaction_by_reference(db, reference=internal_reference)
        if not transaction:
            print(f"Transaction not found for Kora reference {internal_reference}")
            return {"status": "success", "message": "Unknown transaction reference."} # 200 OK so Kora stops retrying
            
        # Idempotency Check: Is it still pending (0)?
        if transaction.status != 0:
            print(f"Transaction {internal_reference} already processed (Status: {transaction.status})")
            return {"status": "success", "message": "Duplicate event, already processed."}

        # --- A. TRANSFER SUCCESSFUL ---
        if event_type == "transfer.success":
            update_transaction(
                db, 
                id=transaction.id, 
                values={
                    'status': 1, # 1 = completed
                    'meta_data': payment_data
                },
                commit=True
            )
            return {"status": "success", "message": "Withdrawal marked successful."}

        # --- B. TRANSFER FAILED (Auto-Refund Logic) ---
        elif event_type == "transfer.failed":
            
            # Lock the source wallet to safely refund
            locked_wallet = get_single_wallet_by_id(db=db, id=transaction.from_wallet_id, for_update=True)
            if not locked_wallet:
                print(f"Critical: Source wallet {transaction.from_wallet_id} missing for refund.")
                return {"status": "error", "message": "Source wallet missing for refund."}
                
            # Perform Refund
            refund_amount = Decimal(str(transaction.total_amount))
            new_balance = Decimal(str(locked_wallet.balance)) + refund_amount
            
            update_wallet(
                db, 
                id=locked_wallet.id, 
                values={'balance': new_balance}, 
                commit=False
            )
            
            # Update the original transaction log to failed (2)
            update_transaction(
                db, 
                id=transaction.id, 
                values={
                    'status': 2,
                    'meta_data': payment_data
                },
                commit=True
            )
            
            # Notify the user that their withdrawal bounced and money was returned
            if transaction.from_user_id:
                user = get_just_single_user_by_id(db, id=transaction.from_user_id)
                if user:
                    e_notification(
                        email=user.email,
                        title="Withdrawal Failed - Refunded",
                        sub_title=f"Your withdrawal of {transaction.amount:,.2f} failed.",
                        recipient_name=user.first_name,
                        msg=f"Your withdrawal of {transaction.amount:,.2f} to {transaction.external_bank_name} was rejected by the bank and has been refunded to your wallet. New balance: {new_balance:,.2f}."
                    )
            
            return {"status": "success", "message": "Transfer failed and wallet refunded."}
            
    except Exception as e:
        db.rollback()
        print(f"Error processing transfer webhook: {e}\n{traceback.format_exc()}")
        return {"status": "error", "message": "Internal server error."}