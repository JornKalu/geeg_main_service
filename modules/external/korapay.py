from typing import Dict, List, Optional
from settings.config import load_env_config
from modules.external.api import send_external_request

config = load_env_config()

def get_korapay_headers() -> Dict:
    """
    Returns the standard headers for KoraPay API requests.
    """
    return {
        "Authorization": f"Bearer {config['korapay_secret_key']}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

def initialize_payment(amount: float, redirect_url: str, reference: str, customer: Dict, description: str = "Payment"):
    """
    Initialize a payment (Checkout).
    Reference: https://developers.korapay.com/reference/initialize-a-charge
    """
    url = f"{config['korapay_url']}/charges/initialize"
    data = {
        "amount": amount,
        "currency": "NGN",
        "reference": reference,
        "redirect_url": redirect_url,
        "customer": customer,
        "description": description,
        "channels": ["card", "bank_transfer", "pay_with_bank"]
    }
    return send_external_request(url=url, headers=get_korapay_headers(), data=data, type=2)

def verify_transaction(reference: str):
    """
    Verify a transaction status.
    Reference: https://developers.korapay.com/reference/verify-transaction
    """
    url = f"{config['korapay_url']}/transactions/verify/{reference}"
    return send_external_request(url=url, headers=get_korapay_headers(), type=1)

def get_balances():
    """
    Fetch account balances.
    Reference: https://developers.korapay.com/reference/fetch-balances
    """
    url = f"{config['korapay_url']}/balances"
    return send_external_request(url=url, headers=get_korapay_headers(), type=1)

def create_virtual_bank_account(
    account_reference: str, 
    account_name: str, 
    bank_code: str,
    customer: Dict, 
    kyc: Dict,
    permanent: bool = True, 
    currency: str = "NGN",
):
    """
    Create a Virtual Bank Account for a customer.
    Reference: https://developers.korapay.com/reference/create-a-virtual-bank-account
    """
    url = f"{config['korapay_url']}/virtual-bank-account"
    data = {
        "account_reference": account_reference,
        "account_name": account_name,
        "customer": customer,
        "permanent": permanent,
        "currency": currency
    }
    if bank_code:
        data["bank_code"] = bank_code
    if kyc:
        data["kyc"] = kyc

    return send_external_request(url=url, headers=get_korapay_headers(), data=data, type=2)

def payout_bank_transfer(amount: float, reference: str, bank_code: str, account_number: str, narration: str = ""):
    """
    Initiate a payout to a bank account.
    Reference: https://developers.korapay.com/docs/payout-via-api
    """
    url = f"{config['korapay_url']}/transactions/disburse"
    data = {
        "reference": reference,
        "destination": {
            "type": "bank_account",
            "amount": amount,
            "currency": "NGN",
            "narration": narration,
            "bank_account": {
                "bank": bank_code,
                "account": account_number
            }
        }
    }
    return send_external_request(url=url, headers=get_korapay_headers(), data=data, type=2)

def get_bank_list():
    """
    Retrieve a list of supported banks for payouts.
    """
    url = f"{config['korapay_url']}/misc/banks?currency=NGN"
    return send_external_request(url=url, headers=get_korapay_headers(), type=1)

def resolve_bank_account(bank_code: str, account_number: str):
    """
    Verify bank account details before payout.
    """
    url = f"{config['korapay_url']}/misc/banks/resolve"
    data = {
        "bank_code": bank_code,
        "account_number": account_number
    }
    return send_external_request(url=url, headers=get_korapay_headers(), data=data, type=2)