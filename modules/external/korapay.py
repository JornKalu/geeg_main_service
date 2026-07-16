from typing import Dict, List, Optional
from settings.config import load_env_config
from modules.external.api import send_external_request

config = load_env_config()

def get_korapay_headers(is_public: bool=False) -> Dict:
    """
    Returns the standard headers for KoraPay API requests.
    """
    key = None
    if is_public == False:
        key = config['korapay_secret_key']
    else:
        key = config['korapay_public_key']
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

def send_korapay_requests(url, data: Dict={}, is_public: bool=False, type: int=1):
    resp = send_external_request(url=url, headers=get_korapay_headers(is_public=is_public), data=data, type=type)
    if resp['status'] == False:
        return {
            'status': False,
            'message': resp['message'],
            'data': None
        }
    else:
        if resp['status_code'] != 200 or resp['status_code'] != 201:
            return {
                'status': False,
                'message': f'Request failed: {resp['status_code']}',
                'data': resp['data']
            }
        else:
            return {
                'status': True,
                'message': 'Success',
                'data': resp['data'],
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
    return send_korapay_requests(url=url, data=data, type=2)

def verify_transaction(reference: str):
    """
    Verify a transaction status.
    Reference: https://developers.korapay.com/reference/verify-transaction
    """
    url = f"{config['korapay_url']}/transactions/verify/{reference}"
    return send_korapay_requests(url=url, type=1)

def get_balances():
    """
    Fetch account balances.
    Reference: https://developers.korapay.com/reference/fetch-balances
    """
    url = f"{config['korapay_url']}/balances"
    return send_korapay_requests(url=url, type=1)

def create_virtual_bank_account(account_reference: str, account_name: str, customer_full_name: str, customer_email: str, customer_bvn: str, customer_nin: str = None, permanent: bool = True):
    """
    Create a Virtual Bank Account for a customer.
    Reference: https://developers.korapay.com/reference/create-a-virtual-bank-account
    """
    url = f"{config['korapay_url']}/virtual-bank-account"
    kyc = {
        "bvn": customer_bvn,
    }
    if customer_nin is not None:
        kyc["nin"] = customer_nin
    data = {
        "account_reference": account_reference,
        "account_name": account_name,
        "bank_code": config['korapay_virtual_account_bank_code'],
        "permanent": permanent,
        "customer": {
            "name": customer_full_name,
            "email": customer_email,
        },
        "kyc": kyc,
    }
    return send_korapay_requests(url=url, data=data, type=2)

def payout_bank_transfer(amount: float, reference: str, bank_code: str, account_number: str, customer_email: str, customer_name: str = None, narration: str = ""):
    """
    Initiate a payout to a bank account.
    Reference: https://developers.korapay.com/docs/payout-via-api
    """
    url = f"{config['korapay_url']}/transactions/disburse"
    
    customer_payload = {"email": customer_email}
    if customer_name:
        customer_payload["name"] = customer_name

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
            },
            "customer": customer_payload
        }
    }
    return send_korapay_requests(url=url, data=data, type=2)

def get_bank_list():
    """
    Retrieve a list of supported banks for payouts.
    """
    url = f"{config['korapay_url']}/misc/banks?currency=NGN"
    return send_korapay_requests(url=url, is_public=True, type=1)

def resolve_bank_account(bank_code: str, account_number: str):
    """
    Verify bank account details before payout.
    """
    url = f"{config['korapay_url']}/misc/banks/resolve"
    data = {
        "bank": bank_code,
        "account": account_number
    }
    return send_korapay_requests(url=url, data=data, type=2)