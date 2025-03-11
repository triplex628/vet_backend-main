from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from src.database import get_db
from src.models.payment import Payment
from src.models.user import User
from datetime import datetime, timezone
import json
import logging

router = APIRouter()

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


SUBSCRIPTION_MAPPING = {
    "va_m_199": "MONTHLY",
    "va_m_6": "HALF_YEARLY",
    "va_m_12": "YEARLY",
    "calculator_1": "CALCULATOR_MONTH",
    "calculator_12": "CALCULATOR_YEAR",
}

@router.post("/revenuecat/webhook")
async def revenuecat_webhook(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
        logger.info(f"RECEIVED RevenueCat WEBHOOK PAYLOAD:\n{json.dumps(data, indent=2)}")

        event_data = data.get("event", {})
        app_user_id = event_data.get("original_app_user_id")  
        product_id = event_data.get("product_id")
        expiration_at_ms = event_data.get("expiration_at_ms")
        
        if not app_user_id:
            raise HTTPException(status_code=400, detail="Missing app_user_id in webhook data")

        expiration_at = datetime.utcfromtimestamp(expiration_at_ms / 1000).replace(tzinfo=timezone.utc) if expiration_at_ms else None

        subscription_type = SUBSCRIPTION_MAPPING.get(product_id, "UNKNOWN")
        if subscription_type == "UNKNOWN":
            raise HTTPException(status_code=400, detail=f"Unknown subscription type for product_id: {product_id}")

        logger.info(f"User ID: {app_user_id}, Subscription Type: {subscription_type}")

        user = db.query(User).filter(User.revenuecat_id == app_user_id).first()

        if not user:
            logger.error(f"User with RevenueCat ID {app_user_id} not found in DB")
            raise HTTPException(status_code=404, detail=f"User with RevenueCat ID {app_user_id} not found")

        payment = db.query(Payment).filter(Payment.user_id == user.id, Payment.payment_system == "RevenueCat").first()

        if payment:
            payment.subscription_type = subscription_type
            payment.expiration_date = expiration_at
        else:
            new_payment = Payment(
                user_id=user.id,
                payment_system="RevenueCat",
                subscription_type=subscription_type,
                expiration_date=expiration_at
            )
            db.add(new_payment)

        user.is_subscribed = True
        db.commit()
        
        return {"status": "success", "message": "Subscription updated"}

    except HTTPException as http_exc:
        logger.error(f"HTTP ERROR: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.error(f"INTERNAL ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")




