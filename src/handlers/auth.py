from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src import schemas
from src import services
from src import database
from src.utils import exceptions
from pydantic import BaseModel
from src.models.user import User

router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    password: str
    revenuecat_id: str | None = None  

@router.post("/create", response_model=schemas.Token)
def login_for_access_token(
    login_data: LoginRequest,  
    db: Session = Depends(database.get_db) 
):
    print("запрос на авторизацию")

    email = services.auth.authenticate_user(db, login_data.email, login_data.password)
    if email is None:
        raise exceptions.credentials_exception

    user = db.query(User).filter(User.email == email).first()

    if login_data.revenuecat_id and not user.revenuecat_id:
        user.revenuecat_id = login_data.revenuecat_id
        db.commit()

    access_token = services.auth.create_access_token(db, {'sub': email})
    
    return {'access_token': access_token, 'token_type': 'bearer'}

