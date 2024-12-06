import random

from sqlalchemy.orm import Session
from src import repositories
from src import schemas
from src.utils import email


def get_user_by_email(db: Session, email: str) -> schemas.User | None:
    return repositories.get_user_by_email(db, email)


async def create_user(db: Session, data: schemas.UserAuth) -> schemas.User | None:
    approve_code = random.randrange(1000, 9999)
    await email.send_email_approve(data.email, str(approve_code))
    return repositories.create_user(db, schemas.UserCreate(email=data.email, password=data.password,
                                                           approve_code=approve_code))


def set_purchased_user(db: Session, user_id: int, is_purchased: bool):
    repositories.user.set_purchase_user(db, user_id, is_purchased)


def set_subscribed_user(db: Session, user_id: int, is_purchased: bool):
    repositories.user.set_subscribed_user(db, user_id, is_purchased)


def approve_user(db: Session, user_id: int, code: int) -> bool:
    return repositories.approve_user(db, user_id, code)


async def request_reset_password_user(db: Session, user_email: str) -> bool:
    reset_code = random.randrange(1000, 9999)
    result = repositories.request_reset_password_user(db, user_email=user_email, code=reset_code)
    if result:
        await email.send_email_password_reset(user_email, str(reset_code))
        return True
    return False


def confirm_reset_password_user(db: Session, user_email: str, code: int, new_password: str) -> bool:
    return repositories.confirm_reset_password_user(db, user_email, code, new_password)


def get_user_subscription_status(db: Session, user_id: int):
    
    user = get_user_by_id(db, user_id)


    active_subscription = get_active_subscription(db, user_id)
    if active_subscription and active_subscription.subscription_type == SubscriptionType.LIFETIME:
        return {
            "active": True,
            "expires": None,
            "type": "lifetime",
        }
    

    if active_subscription:
        return {
            "active": True,
            "expires": active_subscription.expiration_date,
            "type": active_subscription.subscription_type.value,
        }

    return {"active": False, "expires": None, "type": None}