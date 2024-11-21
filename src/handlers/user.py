from urllib import parse

from fastapi import APIRouter, Depends, Body, Query
from sqlalchemy.orm import Session
from src import schemas
from src import services
from src import database
from src.utils import exceptions
from . import dependencies

router = APIRouter()


@router.get('/me', response_model=schemas.User)
def get_users_me(user: schemas.User = Depends(dependencies.get_current_active_user)):
    return user


@router.post('/registration', response_model=schemas.Token)
async def registration_user(data: schemas.UserAuth = Body(...), db: Session = Depends(database.get_db)):
    user = await services.user.create_user(db, data)
    if user is None:
        raise exceptions.bad_request_exception('User with this email already exists')
    access_token = services.auth.create_access_token(db, {'sub': user.email})
    return {'access_token': access_token, 'token_type': 'bearer'}


@router.post('/approve', status_code=200)
def approve_user(data: schemas.UserApproveCode = Body(...),
                 user: schemas.User = Depends(dependencies.get_current_active_user),
                 db: Session = Depends(database.get_db)):
    if services.user.approve_user(db, user_id=user.id, code=data.code):
        return 'successful'
    else:
        raise exceptions.bad_request_exception("bad request")


@router.post('/request_reset_password', status_code=200)
async def request_reset_password_user(data: schemas.UserEmail = Body(...), db: Session = Depends(database.get_db)):
    if await services.user.request_reset_password_user(db, data.email):
        return 'successful'
    else:
        raise exceptions.not_found_exception("user not found")


@router.post('/confirm_reset_password', status_code=200)
def confirm_reset_password_user(data: schemas.UserConfirmResetPassword = Body(...),
                                db: Session = Depends(database.get_db)):
    if services.user.confirm_reset_password_user(db, data.email, data.code, data.new_password):
        return 'successful'
    else:
        raise exceptions.bad_request_exception('bad request')


@router.patch('/subscribed', status_code=200)
def set_subscribed_user(is_subscribed: bool = Query(True, title='subscribed'),
                        user: schemas.User = Depends(dependencies.get_current_active_user),
                        db: Session = Depends(database.get_db)):
    services.user.set_subscribed_user(db, user.id, is_subscribed)
    return 'successful'


@router.patch('/purchased', status_code=200)
def set_purchased_user(is_purchased: bool = Query(True, title='purchased'),
                       user: schemas.User = Depends(dependencies.get_current_active_user),
                       db: Session = Depends(database.get_db)):
    services.user.set_purchased_user(db, user.id, is_purchased)
    return 'successful'
