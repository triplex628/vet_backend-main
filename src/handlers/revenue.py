from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session, joinedload
from src.database import get_db
from src.schemas.subscription import SubscriptionRequest, SubscriptionResponse, SubscriptionStatus, PurchaseResponse, PaymentResponse, CancelSubscriptionRequest
from src.models.payment import SubscriptionType, Payment, PaymentTracking
from src.repositories.user import get_user_by_id
from datetime import datetime
from src.models.user import User
from datetime import datetime, timedelta, timezone
from src import database
import uuid
import requests
from typing import List
from src.utils.yookassa_service import YookassaService
from src.utils.prodamus_service import ProdamusService
from fastapi.responses import JSONResponse

import logging
router = APIRouter()

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

@router.post("/revenuecat/webhook")
async def revenuecat_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()
    logger.info(f"Received RevenueCat webhook payload: {payload}")
    print(f"RECEIVED RevenueCat WEBHOOK PAYLOAD: {payload}")
    event_type = payload.get("event", None)
    user_id = payload.get("app_user_id", None)

    if not user_id:
        logger.warning("User ID not provided in payload")
        raise HTTPException(status_code=400, detail="User ID not provided")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.warning(f"User not found: {user_id}")
        raise HTTPException(status_code=404, detail="User not found")

    if event_type == "INITIAL_PURCHASE" or event_type == "RENEWAL":
        expiration_date_str = payload.get("expiration_at")
        expiration_date = datetime.fromisoformat(expiration_date_str).replace(tzinfo=timezone.utc)
        user.is_subscribed = True

        VALID_SUBSCRIPTIONS = {
            "premium_monthly": "MONTHLY",
            "premium_half_yearly": "HALF_YEARLY",
            "premium_yearly": "YEARLY",
            "monthly": "MONTHLY",
            "half_yearly": "HALF_YEARLY",
            "yearly": "YEARLY",
            "calculator_monthly": "CALCULATOR_MONTH",
            "calculator_yearly": "CALCULATOR_YEAR",
        }

        subscription_type_raw = payload.get("product_id")
        subscription_type = VALID_SUBSCRIPTIONS.get(subscription_type_raw)

        if not subscription_type:
            logger.error(f"Invalid subscription type: {subscription_type_raw}")
            raise HTTPException(status_code=400, detail=f"Invalid subscription type: {subscription_type_raw}")

        payment = Payment(
            user_id=user.id,
            payment_system="RevenueCat",
            subscription_type=subscription_type, 
            expiration_date=expiration_date
        )

        db.add(payment)
        db.commit()
        
        logger.info(f"Subscription activated for user {user.id}: {subscription_type}, expires on {expiration_date}")
        return {"message": "Subscription activated", "user_id": user.id, "subscription_type": subscription_type, "expiration_date": expiration_date.isoformat()}

    elif event_type == "CANCELLATION":
        user.is_subscribed = False
        db.commit()
        logger.info(f"Subscription cancelled for user {user.id}")
        return {"message": "Subscription cancelled", "user_id": user.id}

    logger.info(f"Event processed: {event_type}")
    return {"message": "Event processed", "event_type": event_type}


