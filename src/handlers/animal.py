from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from src import schemas
from src import services
from src import database
from . import dependencies

router = APIRouter()


@router.get('/', status_code=status.HTTP_200_OK)
def get_animals(user: schemas.User = Depends(dependencies.get_current_active_user),
                db: Session = Depends(database.get_db)):
    return services.animal.get_animals(db)
