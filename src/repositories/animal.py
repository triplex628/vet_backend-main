from sqlalchemy import text
from sqlalchemy.orm import Session
from src import schemas


def get_animals(db: Session) -> list[schemas.Animal]:
    result = db.execute(text("""SELECT id, name FROM animals""")).mappings().all()
    animals: list[schemas.Animal] = []
    for r in result:
        animals.append(schemas.Animal(id=r.get('id'), name=r.get('name')))
    return result