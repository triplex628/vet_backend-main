import asyncio
from datetime import datetime
from sqlalchemy.orm import Session
from src.database import SessionLocal
from src.models.user import User
from src.models.users_payments import UserPayment

async def check_expired_subscriptions():
    """
    Проверка подписок через SQL-запрос.
    """
    while True:
        try:
            
            db: Session = SessionLocal()

            now = datetime.utcnow()

            # Отключаем подписку на калькулятор, если срок истёк
            db.query(User).filter(
                User.id.in_(
                    db.query(UserPayment.user_id)
                    .filter(UserPayment.expiration_date < now)
                    .filter(UserPayment.subscription_type.in_(["CALCULATOR_MONTH", "CALCULATOR_YEAR"]))
                )
            ).update({User.is_subscribed_calc: False}, synchronize_session=False)

            # Отключаем обычную подписку, если срок истёк
            db.query(User).filter(
                User.id.in_(
                    db.query(UserPayment.user_id)
                    .filter(UserPayment.expiration_date < now)
                    .filter(UserPayment.subscription_type.notin_(["CALCULATOR_MONTH", "CALCULATOR_YEAR"]))
                )
            ).update({User.is_subscribed: False}, synchronize_session=False)

            db.commit()  
            db.close()

            

        except Exception as e:
            print(f"Ошибка проверки подписок: {e}")

        await asyncio.sleep(86400)  