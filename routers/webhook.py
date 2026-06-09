from fastapi import APIRouter, Request, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.db import get_session
from modules.transactions.hook import verify_korapay_signature, process_korapay_event

router = APIRouter(
    prefix="/webhook",
    tags=["Webhook"]
)

@router.post("/korapay")
async def korapay_webhook(request: Request, db: Session = Depends(get_session)):
    body = await request.body()
    headers = request.headers

    if not verify_korapay_signature(body, headers):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    payload = await request.json()
    return process_korapay_event(db, payload)