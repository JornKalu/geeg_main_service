from typing import Dict, List, Any
from sqlalchemy.orm import Session
from database.model import get_transactions, get_single_transaction_by_id
from fastapi_pagination.ext.sqlalchemy import paginate

def retrieve_transactions(db: Session, filters: Dict={}):
	data = get_transactions(db=db, filters=filters)
	return paginate(data)

def retrieve_single_transaction(db: Session, id: int=0):
	transaction = get_single_transaction_by_id(db=db, id=id)
	if transaction is None:
		return {
			'status': False,
			'message': 'Transaction not found',
			'data': None
		}
	else:
		return {
			'status': True,
			'message': 'Success',
			'data': transaction
		}
