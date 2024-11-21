from sqlalchemy.orm import Session
from src import repositories
from src import schemas


def get_global_drugs_with_favorite(db: Session, user: schemas.User) -> list[schemas.Drug]:
    return repositories.get_all_global_drugs_with_favorite(db, user.id)


def set_favorite_global_drug(db: Session, user: schemas.User, drug_id: int, is_favorite: bool = True):
    repositories.set_favorite_global_drug(db, user.id, drug_id, is_favorite)


def create_users_drug(db: Session, user: schemas.User, data: schemas.DrugCreate):
    return repositories.create_user_drug(db, user.id, data)


def get_users_drugs(db: Session, user: schemas.User) -> list[schemas.Drug]:
    return repositories.get_all_user_drugs(db, user.id)


def set_favorite_users_drug(db: Session, user: schemas.User, drug_id: int, is_favorite: bool = True) -> bool:
    is_successful = repositories.set_favorite_user_drug(db, user.id, drug_id, is_favorite)
    return bool(is_successful)


def partial_update_users_drug(db: Session, user: schemas.User, drug_id: int, data: schemas.DrugPatchUpdate):
    repositories.partial_update_drug(db, user.id, drug_id, data)


def delete_users_drug(db: Session, user: schemas.User, drug_id: int):
    repositories.delete_user_drug(db, user.id, drug_id)