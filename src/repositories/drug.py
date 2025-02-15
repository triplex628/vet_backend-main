from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from src import models
from src import schemas
from src.utils import exceptions


def check_is_global_drug(db: Session, drug_id: int) -> Optional[bool]:
    return db.execute(text("""SELECT drugs.is_global FROM drugs WHERE id = :drug_id"""),
                      {'drug_id': drug_id}).scalar()


def get_all_global_drugs(db: Session) -> list[schemas.Drug]:
    """Получить все ГЛОБАЛЬНЫЕ лекарства"""
    stmt = select(models.Drug).options(joinedload(models.Drug.animals)).where(models.Drug.is_global == True)
    result = db.execute(stmt)
    drugs: list[schemas.Drug] = []
    for row in result.unique():
        drug_model: models.Drug = row[0]
        drug: schemas.Drug = schemas.Drug.from_orm(drug_model)
        drugs.append(drug)
    return drugs


def get_all_global_drugs_with_favorite(db: Session, user_id: int) -> list[schemas.Drug]:
    """Получить все ГЛОБАЛЬНЫЕ лекарства с отметками favorite для пользователя"""
    results = db.execute(text("""
SELECT drugs.id, drugs.name, drugs.description, du.is_favorite, animals.id AS animal_id, animals.name AS animal_name
FROM drugs
LEFT JOIN drugs_users AS du ON drugs.id = du.drug_id AND du.user_id = :user_id
LEFT JOIN (drugs_animals AS da INNER JOIN animals ON da.animal = animals.id) ON drugs.id = da.drug
WHERE drugs.is_global = True ORDER BY du.is_favorite, drugs.name;
"""), {'user_id': user_id}).mappings().all()
    drug_list: list[schemas.Drug] = []
    # переменная для предположения необходимости парсинга следующего животного. Либо None, либо id предыдущего лекарства
    maybe_animal: Optional[int] = None
    for result in results:
        if maybe_animal is not None and result.get('id') == maybe_animal:
            animal = schemas.Animal(id=result.get('animal_id'), name=result.get('animal_name'))
            drug_list[-1].animals.append(animal)
            continue
        maybe_animal = None
        drug = schemas.Drug(id=result.get('id'), name=result.get('name'))
        drug.description = result.get('description')
        drug.is_favorite = result.get('is_favorite') or False
        if result.get('animal_id') is not None:
            animal = schemas.Animal(id=result.get('animal_id'), name=result.get('animal_name'))
            drug.animals = [animal]
            maybe_animal = drug.id
        drug_list.append(drug)
    return drug_list


def get_all_user_drugs(db: Session, user_id: int) -> list[schemas.Drug]:
    """Получить лекарства ПОЛЬЗОВАТЕЛЯ"""
    stmt = select(models.Drug, models.DrugUser.is_favorite) \
        .options(joinedload(models.Drug.animals)) \
        .join(models.DrugUser) \
        .where(models.Drug.is_global == False, models.DrugUser.user_id == user_id) \
        .order_by(models.DrugUser.is_favorite.desc())
    result = db.execute(stmt)
    drugs: list[schemas.Drug] = []
    for row in result.unique():
        drug_model: models.Drug = row[0]
        is_favorite: bool = row[1]
        drug: schemas.Drug = schemas.Drug.from_orm(drug_model)
        drug.is_favorite = is_favorite
        drugs.append(drug)
    return drugs


def create_user_drug(db: Session, user_id: int, drug: schemas.DrugCreate) -> schemas.Drug:
    """Создать лекарство ПОЛЬЗОВАТЕЛЯ"""
    drug_model: models.Drug = models.Drug(name=drug.name, description=drug.description, is_global=False)
    db.add(drug_model)
    db.flush()
    # добавляем M2M with User
    try:
        drug_user_model: models.DrugUser = models.DrugUser(drug_id=drug_model.id, user_id=user_id,
                                                           is_favorite=drug.is_favorite)
        db.add(drug_user_model)
        db.flush()
    except IntegrityError:
        raise exceptions.not_found_exception('User not found')
    # добавляем M2M with Animal
    if drug.animals is not None:
        try:
            raw_sql = text('INSERT INTO drugs_animals (drug, animal) VALUES (:drug, :animal)')
            db.execute(raw_sql, [{'drug': drug_model.id, 'animal': i} for i in drug.animals])
        except IntegrityError:
            raise exceptions.not_found_exception(f'Animal not found')
    db.commit()
    return schemas.Drug.from_orm(drug_model)


def partial_update_drug(db: Session, user_id: int, drug_id: int, drug: schemas.DrugPatchUpdate):
    """PATCH UPDATE для лекарств ПОЛЬЗОВАТЕЛЯ"""
    # проверяем, что это ПОЛЬЗОВАТЕЛЬСКОЕ лекарство
    is_global = check_is_global_drug(db, drug_id)
    if is_global is None:
        raise exceptions.not_found_exception()
    if is_global is True:
        raise exceptions.bad_request_exception('it is not user drug')
    # проверяем, что лекарство принадлежит пользователю (чтобы не наглели)
    result = db.execute(
        text("""SELECT EXISTS(SELECT 1 FROM drugs_users WHERE drug_id = :drug_id AND user_id = :user_id);"""),
        {'drug_id': drug_id, 'user_id': user_id}).scalar()
    if result is False:
        raise exceptions.not_authorized_exception('You are not the owner of drug')
    drug_dict = drug.dict(exclude_unset=True)
    # обновляем имя и описание
    raw_sql = None
    name = drug_dict.get('name')
    description = drug_dict.get('description')
    if name is not None and description is not None:
        raw_sql = text("""UPDATE drugs SET name = :name, description = :description WHERE id = :drug_id""")
    elif description is None and name is not None:
        raw_sql = text("""UPDATE drugs SET name = :name WHERE id = :drug_id""")
    elif name is None and description is not None:
        raw_sql = text("""UPDATE drugs SET description = :description WHERE id = :drug_id""")
    drug_dict['drug_id'] = drug_id
    if raw_sql is not None:
        db.execute(raw_sql, drug_dict)

    # обновляем животных
    animal_ids = drug_dict.get('animals')
    if animal_ids is not None:
        # Получаем текущие связи
        existing_animals = db.execute(
            """SELECT animal FROM drugs_animals WHERE drug = :drug_id""",
            {'drug_id': drug_id}
        ).fetchall()
        
        existing_animals = {row[0] for row in existing_animals}

        # Находим новых животных, которых ещё нет в БД
        new_animals = set(animal_ids) - existing_animals

        # Добавляем только новые связи
        values = [{'drug_id': drug_id, 'animal_id': animal_id} for animal_id in new_animals]
        if values:
            try:
                db.execute(text("""INSERT INTO drugs_animals (drug, animal) VALUES (:drug_id, :animal_id)"""),
                        values)
            except IntegrityError:
                raise exceptions.not_found_exception(f'Animal not found')

    db.commit()



def set_favorite_user_drug(db: Session, user_id: int, drug_id: int, is_favorite: bool = True) -> int:
    """Меняет свойство is_favorite для ПОЛЬЗОВАТЕЛЬСКИХ лекарств. Если возвращает 0, значит ничего не было обновлено"""
    # проверяем, что это ПОЛЬЗОВАТЕЛЬСКОЕ лекарство
    is_global = check_is_global_drug(db, drug_id)
    if is_global is None:
        raise exceptions.not_found_exception()
    if is_global is True:
        raise exceptions.bad_request_exception('it is not user drug')
    result = db.execute(text("""
                        UPDATE drugs_users
                        SET is_favorite = :favorite
                        WHERE drug_id = :drug_id
                          AND user_id = :user_id
                        """),
                        {'favorite': is_favorite, 'drug_id': drug_id, 'user_id': user_id})
    db.commit()
    return result.rowcount


def set_favorite_global_drug(db: Session, user_id: int, drug_id: int, is_favorite: bool = True):
    """Меняет свойство is_favorite для ГЛОБАЛЬНЫХ лекарств"""
    # проверяем, что это ГЛОБАЛЬНОЕ лекарство
    is_global = check_is_global_drug(db, drug_id)
    if is_global is None:
        raise exceptions.not_found_exception()
    if is_global is False:
        raise exceptions.bad_request_exception('it is not global drug')

    result = db.execute(text("""SELECT drugs_users.is_favorite
                                                    FROM drugs_users
                                                    WHERE drug_id = :drug_id
                                                      AND user_id = :user_id
                                                """),
                        {'drug_id': drug_id, 'user_id': user_id}).scalar()

    if is_favorite is True:
        # идеальный сценарий
        if result is None:
            db.execute(
                text("""INSERT INTO drugs_users (drug_id, user_id, is_favorite) VALUES (:drug_id, :user_id, true)"""),
                {'drug_id': drug_id, 'user_id': user_id})
            db.commit()
            return
        # хреновый сценарий
        elif result is False:
            db.execute(
                text("""UPDATE drugs_users SET is_favorite = true WHERE user_id = :user_id AND drug_id = :drug_id"""),
                {'user_id': user_id, 'drug_id': drug_id})
            db.commit()
            return
        elif result is True:
            return

    if is_favorite is False:
        # если такая запись есть в таблице drugs_users
        if result is not None:
            db.execute(text("""DELETE FROM drugs_users WHERE user_id = :user_id AND drug_id = :drug_id"""),
                       {'user_id': user_id, 'drug_id': drug_id})
            db.commit()
            return
        else:
            return


def delete_user_drug(db: Session, user_id: int, drug_id: int):
    """Удаление лекарства ПОЛЬЗОВАТЕЛЯ"""
    # проверяем, что это ПОЛЬЗОВАТЕЛЬСКОЕ лекарство
    is_global = check_is_global_drug(db, drug_id)
    if is_global is None:
        raise exceptions.not_found_exception()
    if is_global is True:
        raise exceptions.bad_request_exception('it is not user drug')

    # удаляем связь лекарство-пользователь. Если ничего не найден - выдаем ошибку
    result = db.execute(
        text("""DELETE FROM drugs_users WHERE user_id = :user_id AND drug_id = :drug_id RETURNING drug_id"""),
        {'user_id': user_id, 'drug_id': drug_id}).scalar()
    if result is None:
        raise exceptions.not_authorized_exception('You are not the owner of drug')

    # удаляем связь лекарство-животное.
    db.execute(text("""DELETE FROM drugs_animals WHERE drug = :drug_id"""),
               {'drug_id': drug_id})
    # удаляем лекарство
    db.execute(text('DELETE FROM drugs WHERE id = :drug_id'),
               {'drug_id': drug_id})
    db.commit()
