from typing import Optional
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from src import schemas
from src.models.user import User


def get_user_by_id(db: Session, id: int) -> Optional[User]:
    print(f"GET_USER_BY_ID: Looking for user with id={id}")
    user = db.query(User).filter(User.id == id).first()
    print(f"User found: {user}")
    return user




def get_user_with_password_by_email(db: Session, email: str) -> Optional[schemas.UserAuth]:
    result = db.execute(text("""SELECT email, password FROM users WHERE email = :email"""),
                        {'email': email}).mappings().first()
    if result is None:
        return None
    return schemas.UserAuth(email=result.get('email'), password=result.get('password'))


def get_user_by_email(db: Session, email: str) -> Optional[schemas.User]:
    result = db.execute(
        text(
            """SELECT id, email, is_active, is_purchased, is_admin, is_subscribed, is_approved, is_subscribed_calc 
            FROM users WHERE email = :email"""),
        {'email': email}).mappings().first()
    if result is None:
        return None

    print("User query result:", result)
    return schemas.User(id=result.get('id'), email=result.get('email'), is_purchased=result.get('is_purchased'),
                        is_admin=result.get('is_admin'), is_active=result.get('is_active'),
                        is_subscribed=result.get('is_subscribed'), is_approved=result.get('is_approved'), is_subscribed_calc=result.get('is_subscribed_calc'))


def create_user(db: Session, user: schemas.UserCreate) -> schemas.User | None:
    try:
        result = db.execute(
            text("""
                INSERT INTO users (email, password, is_active, is_purchased, is_admin, is_subscribed, last_code, is_approved) 
                VALUES (:email, :password, :is_active, :is_purchased, :is_admin, :is_subscribed, :last_code, :is_approved)
                RETURNING id, email, is_purchased, is_subscribed
                """),
            {'email': user.email, 'password': user.password, 'is_active': True, 'is_purchased': user.is_purchased,
             'is_admin': False, 'is_subscribed': user.is_subscribed, 'is_approved': False,
             'last_code': user.approve_code}).mappings().first()
        db.commit()
        return schemas.User(id=result.get('id'), email=result.get('email'), is_purchased=result.get('is_purchased'),
                            is_active=True, is_subscribed=result.get('is_subscribed'), is_approved=False)
    except IntegrityError:
        # пользователь с таким email уже есть
        return None


def approve_user(db: Session, user_id: int, code: int) -> bool:
    try:
        result = db.execute(text("""UPDATE users SET is_approved = true, last_code = NULL WHERE id = :user_id AND 
        last_code = :code
        RETURNING *;"""),
                            {'user_id': user_id, 'code': code})
        db.commit()
        # todo:нужно проверить!!!!
        if len(result.all()) == 0:
            return False
        return True
    except IntegrityError:
        return False


def request_reset_password_user(db: Session, user_email: str, code: int) -> bool:
    try:
        result = db.execute(text("""UPDATE users SET last_code = :code WHERE email = :user_email RETURNING *"""),
                            {'user_email': user_email, 'code': code})
        db.commit()
        if len(result.all()) == 0:
            return False
        return True
    except IntegrityError:
        return False


def confirm_reset_password_user(db: Session, user_email: str, code: int, new_password: str) -> bool:
    try:
        result = db.execute(text(
            """UPDATE users SET password = :new_password, last_code = NULL WHERE email = :user_email AND last_code = 
            :code RETURNING *"""),
            {'user_email': user_email, 'code': code, 'new_password': new_password})
        db.commit()
        if len(result.all()) == 0:
            return False
        return True
    except IntegrityError:
        return False


def set_purchase_user(db: Session, user_id: int, is_purchased: bool):
    try:
        db.execute(text("""UPDATE users SET is_purchased = :is_purchased WHERE id = :user_id"""),
                   {'is_purchased': is_purchased, 'user_id': user_id})
        db.commit()
    except IntegrityError:
        # todo:обработать 404 ошибка.Пользователя нет
        print('todo:обработать 404 ошибка.Пользователя нет')
        return


def set_subscribed_user(db: Session, user_id: int, is_subscribed: bool):
    try:
        db.execute(text("""UPDATE users SET is_subscribed = :is_subscribed WHERE id = :user_id"""),
                   {'is_subscribed': is_subscribed, 'user_id': user_id})
        db.commit()
    except IntegrityError:
        # todo:обработать 404 ошибка.Пользователя нет
        print('todo:обработать 404 ошибка.Пользователя нет')
        return


def set_uuid_token(db: Session, user_id: int, uuid: str):
    try:
        db.execute(text("""UPDATE users SET uuid_access_token = :uuid WHERE id = :user_id"""),
                   {"uuid": uuid, "user_id": user_id})
        db.commit()
    except IntegrityError:
        return


def get_uuid_token(db: Session, user_id: int) -> str | None:
    result = db.execute(text("""SELECT uuid_access_token FROM users WHERE id = :user_id"""),
                        {"user_id": user_id}).mappings().first()
    if result is None:
        return None
    return result.get('uuid_access_token')
