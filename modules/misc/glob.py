from typing import Dict, List
from sqlalchemy.orm import Session
from database.model import get_countries, get_single_country_by_id, get_currencies, get_single_currency_by_id
from modules.utils.tools import process_schema_dictionary
from fastapi_pagination.ext.sqlalchemy import paginate

def retrieve_countries(db: Session, filters: Dict={}):
    data = get_countries(db=db, filters=filters)
    return paginate(data)

def retrieve_single_country(db: Session, id: int=0):
    country = get_single_country_by_id(db=db, id=id)
    if country is None:
        return {
            'status': False,
            'message': 'Country not found',
            'data': None
        }
    else:
        return {
            'status': True,
            'message': 'Success',
            'data': country
        }

def retrieve_currencies(db: Session, filters: Dict={}):
    data = get_currencies(db=db, filters=filters)
    return paginate(data)

def retrieve_single_currency(db: Session, id: int=0):
    currency = get_single_currency_by_id(db=db, id=id)
    if currency is None:
        return {
            'status': False,
            'message': 'Currency not found',
            'data': None
        }
    else:
        return {
            'status': True,
            'message': 'Success',
            'data': currency
        }
