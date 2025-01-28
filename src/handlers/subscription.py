from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from src.database import get_db
from src.schemas.subscription import SubscriptionRequest, SubscriptionResponse, SubscriptionStatus, PurchaseResponse, PaymentResponse, CancelSubscriptionRequest
from src.models.payment import SubscriptionType, Payment, PaymentTracking
from src.repositories.user import get_user_by_id
from datetime import datetime
from src.models.user import User
from datetime import datetime, timedelta
from src import database
import uuid
import requests
from typing import List
from src.utils.yookassa_service import YookassaService
from src.utils.prodamus_service import ProdamusService
from fastapi.responses import JSONResponse


import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])

@router.get("/available", response_model=SubscriptionResponse)
def get_available_subscriptions(user_id: int, db: Session = Depends(database.get_db)):
    """
    Возвращает список доступных подписок в зависимости от текущей подписки пользователя.
    """
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

   
    lifetime_payment = (
        db.query(Payment)
        .filter(
            Payment.user_id == user_id,
            Payment.subscription_type == SubscriptionType.LIFETIME.name
        )
        .first()    
    )

   
    if lifetime_payment:
        options = [
            {
                "type": sub_type.value,
                "price": sub_type.get_price,
                "title": sub_type.title,
            }
            for sub_type in [
                SubscriptionType.CALCULATOR_MONTH,
                SubscriptionType.CALCULATOR_YEAR,
            ]
        ]
    else:
        
        options = [
            {
                "type": sub_type.value,
                "price": sub_type.get_price,
                "title": sub_type.title,
            }
            for sub_type in [
                SubscriptionType.MONTHLY,
                SubscriptionType.HALF_YEARLY,
                SubscriptionType.YEARLY,
            ]
        ]

    return {"subscriptions": options}




@router.get("/status", response_model=List[SubscriptionStatus])
def get_subscription_status(user_id: int, db: Session = Depends(get_db)):
    """
    Проверяет статус активных подписок пользователя.
    """
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    
    active_payments = (
        db.query(Payment)
        .filter(Payment.user_id == user_id, Payment.expiration_date > datetime.utcnow())
        .all()
    )

    if not active_payments:
        return JSONResponse(
            content={"message": "The user has no active subscriptions"}, 
            status_code=200
        )

   
    subscriptions = [
        {
            "active": True,
            "type": payment.subscription_type.value, 
            "expires": payment.expiration_date.isoformat(),
        }
        for payment in active_payments
    ]

    return subscriptions

  




@router.post("/purchase", status_code=200)
def purchase_subscription(subscription: SubscriptionRequest, db: Session = Depends(database.get_db)):
    """
    Создаёт запрос на покупку подписки.
    """
    print("Available subscription types:", [sub_type.value for sub_type in SubscriptionType])
    print("Received subscription type:", subscription.type)

    
    try:
       
        sub_type = next((st for st in SubscriptionType if st.value == subscription.type.strip().lower()), None)
        if not sub_type:
            raise ValueError(f"Invalid subscription type: {subscription.type}")
        print("Parsed subscription type:", sub_type)
    except ValueError as e:
        print(e)
        raise HTTPException(status_code=400, detail="Invalid subscription type")

    
    user = db.query(User).filter(User.id == subscription.user_id).first()
    if not user:
        print(f"User with ID {subscription.user_id} not found.")
        raise HTTPException(status_code=404, detail="User not found")

    
    price = sub_type.get_price
    description = f"Подписка {sub_type.title} для VetApp"
    ticket_id = str(uuid.uuid4())

    
    payment_method = subscription.payment_method.lower()
    if payment_method not in ["prodamus", "yookassa"]:
        raise HTTPException(status_code=400, detail="Invalid payment method")

    
    payment_url = None
    try:
        if payment_method == "prodamus":
            #продамус
            payload = {
                "do": "link",
                "order_id": ticket_id,
                "customer_email": user.email,
                "paid_content": description,
                "products[0][name]": description,
                "products[0][quantity]": 1,
                "products[0][price]": price,
            }
            response = requests.get("https://vetapp.payform.ru", params=payload)
            if response.status_code == 200:
                payment_url = response.text
            else:
                print(f"Prodamus error response: {response.text}")
                raise Exception("Failed to generate payment URL for Prodamus")
        elif payment_method == "yookassa":
            #юкасса
            yookassa = YookassaService()
            payment_data = yookassa.create_payment(price=price, return_url="https://yourapp.com/payment/success")
            payment_url = payment_data.get("confirmation_url")
            if not payment_url:
                raise Exception("No confirmation URL in Yookassa response")
    except Exception as e:
        print(f"Error while creating payment: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate payment URL")

    
    payment_tracking = PaymentTracking(
        ticket_id=ticket_id,
        user_id=user.id,
        subscription_type=sub_type.name,
        payment_completed=False
    )
    db.add(payment_tracking)

   
    users_payment = Payment(
        user_id=user.id,
        ticket_id=ticket_id,
        payment_system=payment_method,
        subscription_type=None,  
        expiration_date=None     
    )
    db.add(users_payment)

    db.commit()

    return {
        "payment_url": payment_url,
        "success_url": f"https://yourapp.com/payment/success?ticket_id={ticket_id}",
        "failure_url": f"https://yourapp.com/payment/failure?ticket_id={ticket_id}",
        "ticket_id": ticket_id
    }




@router.post("/payment/success")
def confirm_payment(ticket_id: str, db: Session = Depends(get_db)):
    """
    Подтверждает успешную оплату подписки.
    """
 
    tracking = db.query(PaymentTracking).filter(PaymentTracking.ticket_id == ticket_id).first()
    if not tracking:
        raise HTTPException(status_code=404, detail="Tracking record not found")

  
    if tracking.payment_completed:
        raise HTTPException(status_code=400, detail="Payment already confirmed for this ticket")

    subscription_type = tracking.subscription_type
    if not subscription_type:
        raise HTTPException(status_code=400, detail="Subscription type is not set for this ticket")

    try:

        subscription_duration = get_subscription_duration(subscription_type)
        expiration_date = datetime.utcnow() + subscription_duration
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


    payment = db.query(Payment).filter(Payment.ticket_id == ticket_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found in users_payments")
    
    payment.subscription_type = subscription_type
    payment.expiration_date = expiration_date

    tracking.payment_completed = True

    user = db.query(User).filter(User.id == payment.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if payment.subscription_type == SubscriptionType.CALCULATOR_MONTH.name or payment.subscription_type == SubscriptionType.CALCULATOR_YEAR.name:
        user.is_subscribed_calc = True
    else:
        user.is_purchased = True
        user.is_subscribed = True
    db.add(user)
    db.commit()

    return {
        "detail": "Payment confirmed and subscription activated",
        "subscription_type": subscription_type,
        "expiration_date": expiration_date.isoformat() if expiration_date else "Lifetime"
    }



def get_subscription_duration(subscription_type: str) -> timedelta:
    if subscription_type == "MONTHLY" or subscription_type == "CALCULATOR_MONTH":
        return timedelta(days=30)
    elif subscription_type == "HALF_YEARLY":
        return timedelta(days=182)
    elif subscription_type == "YEARLY" or subscription_type == "CALCULATOR_YEAR":
        return timedelta(days=365)
    elif subscription_type == "LIFETIME":
        return timedelta(days=999999)    
    else:
        raise ValueError("Invalid subscription type")


@router.post("/cancel")
def cancel_subscription(request: CancelSubscriptionRequest, db: Session = Depends(get_db)):
    
    user = get_user_by_id(db, request.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    active_payment = next(
        (p for p in user.payments if p.expiration_date and p.expiration_date > datetime.utcnow()), None
    )
    if not active_payment:
        raise HTTPException(status_code=400, detail="No active subscription to cancel")

    active_payment.expiration_date = datetime.utcnow()  
    user.is_purchased = False
    user.is_subscribed = False
    db.commit()

    return {"detail": "Subscription canceled successfully."}


