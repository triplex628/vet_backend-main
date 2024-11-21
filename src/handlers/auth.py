from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from src import schemas
from src import services
from src import database
from src.utils import exceptions

router = APIRouter()


@router.post("/create", response_model=schemas.Token)
def login_for_access_token(db: Session = Depends(database.get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    email = services.auth.authenticate_user(db, form_data.username, form_data.password)
    if email is None:
        raise exceptions.credentials_exception
    access_token = services.auth.create_access_token(db, {'sub': email})
    return {'access_token': access_token, 'token_type': 'bearer'}
