import requests
from urllib import parse
import uuid

from fastapi import APIRouter, Depends, Body, Query, Header
from sqlalchemy.orm import Session
from src import schemas
from src import models
from src import database
from src.utils import exceptions
from . import dependencies

router = APIRouter()

@router.get('/prodamus_link', status_code=200)
def get_payment_link(db: Session = Depends(database.get_db), user: schemas.User = Depends(dependencies.get_current_active_user)):
    ticket_id = uuid.uuid4()
    payload = {
            "do": "link",
            "order_id": ticket_id,
            "customer_email": user.email,
            "paid_content": "Спасибо за покупку полной версии VetApp",
            "products[0][name]": "Полная версия VetApp",
            "products[0][quantity]": 1,
            "products[0][price]": 100,
            "discount_value": 100
            }
    try:
        response = requests.get("https://vetapp.payform.ru", params=payload)
        if response.status_code == 200:
            db.add(models.Payment(user_id=user.id, ticket_id=ticket_id, payment_system="prodamus"))
            db.commit()
            return {"url": response.text}
    except Exception as e:
        print(e)
        return {"detail": "Something went wrong. Please, try again later"}


@router.post('/06d711bb-8e88-41b4-abcb-dd44ec473b85', status_code=200)
def set_subscribed_user_prodamus(db: Session = Depends(database.get_db),
                                 #signature: str = Depends(dependencies.verify_signature),
                                 data: bytes = Body(...)):
    data = dict(parse.parse_qsl(data.decode('utf-8')))
    ticket_id = data.get('order_num') 
    try:
        payment = db.query(models.Payment).filter(
                models.Payment.ticket_id==ticket_id
                ).first()
        if not payment:
            print(f"Ticket#{ticket_id} not found")
            return {"detail": f"Ticket#{ticket_id} not found"} 
    except Exception as e:
        print(e)
        return {"detail": "Something went wrong. Please, try later"}

    payment.user.is_purchased = True
    for p in payment.user.payments:
        db.delete(p)
    db.commit()
    
    return "sucessfull"
