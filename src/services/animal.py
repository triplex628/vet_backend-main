from sqlalchemy.orm import Session
from src import repositories
from src import schemas


def get_animals(db: Session) -> list[schemas.Animal]:
    return repositories.get_animals(db)
