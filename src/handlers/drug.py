from fastapi import APIRouter, Depends, Body, status, Path, Query
from sqlalchemy.orm import Session
from src import schemas
from src import services
from src import database
from src.utils import exceptions
from . import dependencies

router = APIRouter()


@router.get('/global', response_model=list[schemas.Drug], status_code=status.HTTP_200_OK)
def get_global_drugs_for_user(db: Session = Depends(database.get_db),
                              user: schemas.User = Depends(dependencies.get_current_active_user)):
    return services.drug.get_global_drugs_with_favorite(db, user)


@router.patch('/favorite_global/{drug_id}', status_code=status.HTTP_200_OK)
def set_favorite_global_drug(drug_id: int = Path(..., title='id drug'),
                             is_favorite: bool = Query(True, title='is favorite ?'),
                             db: Session = Depends(database.get_db),
                             user: schemas.User = Depends(dependencies.get_current_active_user)):
    services.drug.set_favorite_global_drug(db, user, drug_id, is_favorite)
    return 'successful'


@router.post('/create', status_code=status.HTTP_201_CREATED, response_model=schemas.Drug)
def create_users_drug(drug: schemas.DrugCreate = Body(...),
                      user: schemas.User = Depends(dependencies.get_current_active_user),
                      db: Session = Depends(database.get_db)):
    return services.drug.create_users_drug(db, user, drug)


@router.get('/users', status_code=status.HTTP_200_OK, response_model=list[schemas.Drug])
def get_users_drugs(user: schemas.User = Depends(dependencies.get_current_active_user),
                    db: Session = Depends(database.get_db)):
    return services.drug.get_users_drugs(db, user)


@router.patch('/favorite_users/{drug_id}', status_code=status.HTTP_200_OK)
def set_favorite_users_drug(drug_id: int = Path(..., title='id drug'),
                            is_favorite: bool = Query(True, title='is favorite ?'),
                            db: Session = Depends(database.get_db),
                            user: schemas.User = Depends(dependencies.get_current_active_user)):
    is_successful = services.drug.set_favorite_users_drug(db, user, drug_id, is_favorite)
    if is_successful is False:
        raise exceptions.bad_request_exception('You are not owner of this drug')
    return 'successful'


@router.patch('/{drug_id}', status_code=status.HTTP_200_OK)
def patch_update_users_drug(drug_id: int = Path(..., title='id drug'),
                            drug: schemas.DrugPatchUpdate = Body(...),
                            db: Session = Depends(database.get_db),
                            user: schemas.User = Depends(dependencies.get_current_active_user)):
    services.drug.partial_update_users_drug(db, user, drug_id, drug)
    return 'successful'


@router.delete('/{drug_id}', status_code=status.HTTP_200_OK)
def delete_users_drug(drug_id: int = Path(..., title='id drug'),
                            db: Session = Depends(database.get_db),
                            user: schemas.User = Depends(dependencies.get_current_active_user)):
    services.drug.delete_users_drug(db, user, drug_id)
    return 'successful'