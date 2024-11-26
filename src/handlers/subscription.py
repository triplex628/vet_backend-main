from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from src.database import get_db
from src.schemas.subscription import SubscriptionRequest, SubscriptionResponse, SubscriptionStatus, PurchaseResponse, PaymentResponse, CancelSubscriptionRequest
from src.models.payment import SubscriptionType, Payment
from src.repositories.user import get_user_by_id
from datetime import datetime
from src.models.user import User
from datetime import datetime, timedelta
from src import database
import uuid
import requests
from typing import List

import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])

@router.get("/available", response_model=SubscriptionResponse)
def get_available_subscriptions(user_id: int, db: Session = Depends(database.get_db)):
    """
    Возвращает список доступных подписок в зависимости от текущей подписки пользователя.
    """
    # Получаем пользователя из базы данных
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Проверяем, есть ли у пользователя пожизненная подписка
    lifetime_payment = (
        db.query(Payment)
        .filter(
            Payment.user_id == user_id,
            Payment.subscription_type == SubscriptionType.LIFETIME.name
        )
        .first()    
    )

    # Если есть пожизненная подписка, возвращаем только подписку на калькулятор
    if lifetime_payment:
        options = [
            {
                "type": sub_type.value,
                "price": sub_type.get_price,
                "title": sub_type.title,
            }
            for sub_type in [
                SubscriptionType.CALCULATOR,
            ]
        ]
    else:
        # Если подписки нет, возвращаем стандартные подписки
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
    
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Найти активную подписку с датой окончания позже текущего времени
    active_payments = (
        db.query(Payment)
        .filter(Payment.user_id == user_id, Payment.expiration_date > datetime.utcnow())
        .all()
    )
    if not active_payments:
        return {"active": False, "expires": None, "type": None}

    subscriptions = []
    for payment in active_payments:
        subscriptions.append({
            "active": True,
            "type": payment.subscription_type.value,
            "expires": payment.expiration_date.isoformat() if payment.expiration_date else "Never",
        })

    return subscriptions
    # return {
    #     "active": True,
    #     "expires": active_payment.expiration_date.isoformat(),
    #     "type": active_payment.subscription_type.value,
    # }




@router.post("/purchase", status_code=200)
def purchase_subscription(subscription: SubscriptionRequest, db: Session = Depends(database.get_db)):
    
    print("Available subscription types:", [sub_type.value for sub_type in SubscriptionType])
    print("Received subscription type:", subscription.type)

    def get_subscription_type(type_value: str) -> SubscriptionType:
        for sub_type in SubscriptionType:
            if sub_type.value == type_value:
                return sub_type
        raise ValueError(f"Invalid subscription type: {type_value}")

    print("Received subscription type:", subscription.type)
    try:
        sub_type = get_subscription_type(subscription.type.lower())
        print("Parsed subscription type:", sub_type)
    except ValueError as e:
        print(e)
        return {"detail": "Invalid subscription type"}
    
    ticket_id = uuid.uuid4()

   
    user = db.query(User).filter(User.id == subscription.user_id).first()
    if not user:
        return {"detail": "User not found"}

    
    try:
        sub_type = get_subscription_type(subscription.type.lower())  
        price = sub_type.get_price  
    except ValueError as e:
        print(e)  
        return {"detail": "Invalid subscription type"}

    # Параметры для запроса к платёжной системе
    payload = {
        "do": "link",
        "order_id": ticket_id,
        "customer_email": user.email,
        "paid_content": f"Подписка {sub_type.title} для VetApp",
        "products[0][name]": f"Подписка {sub_type.title}",
        "products[0][quantity]": 1,
        "products[0][price]": price,
    }

    # Запрос к платёжной системе
    try:
        response = requests.get("https://vetapp.payform.ru", params=payload)
        if response.status_code == 200:
            # Сохранение информации о платеже в базе данных
            db.add(Payment(user_id=user.id, ticket_id=ticket_id, payment_system="prodamus"))
            db.commit()

            # Возврат ссылки на оплату
            return {
                "payment_url": response.text,
                "success_url": f"https://yourapp.com/payment/success?user_id={user.id}&type={subscription.type}",
                "failure_url": f"https://yourapp.com/payment/failure?user_id={user.id}"
            }
    except Exception as e:
        print(e)
        return {"detail": "Failed to generate payment URL. Please, try again later."}


@router.post("/payment/success")
def confirm_payment(user_id: int, type: str, db: Session = Depends(get_db)):
    print(f"Confirm payment called with user_id={user_id}, type={type}")

    user = get_user_by_id(db, user_id)
    if not user:
        print(f"User with id={user_id} not found!")
        raise HTTPException(status_code=404, detail="User not found")

    print(f"User found: {user}")

    try:
        print("Available subscription types:", [sub_type.value for sub_type in SubscriptionType])
        sub_type = next((st for st in SubscriptionType if st.value == type.strip()), None)
        if not sub_type:
            raise ValueError(f"Invalid subscription type: {type}")
        print("Parsed subscription type:", sub_type)
    except ValueError as e:
        print(e)
        raise HTTPException(status_code=400, detail=str(e))

    subscription_type_db = sub_type.name

    new_payment = Payment(
        user_id=user_id,
        subscription_type=subscription_type_db,
        payment_system="prodamus",
        expiration_date=datetime.utcnow() + get_subscription_duration(type),
    )
    

    
    print(f"Before update: is_purchased={user.is_purchased}, is_subscribed={user.is_subscribed}")
    user.is_purchased = True
    user.is_subscribed = True
    db.add(new_payment)
    db.add(user)
    db.commit()
    
    print(f"After update: is_purchased={user.is_purchased}, is_subscribed={user.is_subscribed}")
   

    print("Payment confirmed and subscription activated.")
    return {"detail": "Payment confirmed and subscription activated."}


def get_subscription_duration(subscription_type: str) -> timedelta:
    if subscription_type == "monthly" or subscription_type == "calculator":
        return timedelta(days=30)
    elif subscription_type == "half_yearly":
        return timedelta(days=182)
    elif subscription_type == "yearly":
        return timedelta(days=365)
    elif subscription_type == "lifetime":
        return timedelta(days=999999)    
    else:
        raise ValueError("Invalid subscription type")


@router.post("/cancel")
def cancel_subscription(request: CancelSubscriptionRequest, db: Session = Depends(get_db)):
    
    user = get_user_by_id(db, request.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Проверить, есть ли активная подписка
    active_payment = next(
        (p for p in user.payments if p.expiration_date and p.expiration_date > datetime.utcnow()), None
    )
    if not active_payment:
        raise HTTPException(status_code=400, detail="No active subscription to cancel")

    # Деактивировать подписку
    active_payment.expiration_date = datetime.utcnow()  # Установить дату окончания на текущий момент
    user.is_purchased = False
    user.is_subscribed = False
    db.commit()

    return {"detail": "Subscription canceled successfully."}


