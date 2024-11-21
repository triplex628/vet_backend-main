from typing import Any

from fastadmin import SqlAlchemyModelAdmin, register
from sqlalchemy import text
from src import models
from src import database

class CustomAdminModel(SqlAlchemyModelAdmin):
    async def orm_delete_obj(self, id: int) -> None:
        sessionmaker = self.get_sessionmaker()
        async with sessionmaker() as session:
            obj = await session.get(self.model_cls, id)
            if obj:
                await session.delete(obj)
                await session.commit()

#    async def orm_save_obj(self, id: int , payload: dict) -> Any:
        """This method is used to save orm/db model object.

        :params id: an id of object.
        :params payload: a dict of payload.
        :return: An object.
        """
 #        print("START PROCESS SAVE")
 #        sessionmaker = self.get_sessionmaker()
 #        async with sessionmaker() as session:
 #            if id:
 #                obj = await session.get(self.model_cls, id)
 #                if not obj:
 #                    return None
 #                for k, v in payload.items():
 #                    setattr(obj, k, v)
 #                await session.merge(obj)
 #                await session.commit()
 #            else:
 #                obj = self.model_cls(**payload)
 #                session.add(obj)
 #                await session.commit()
 #            return await session.get(self.model_cls, getattr(obj, self.get_model_pk_name(self.model_cls)))




@register(models.User)
class UserAdminModel(CustomAdminModel):
    list_display = ("id", "email", "is_admin", "is_active", "is_approved",
            "is_subscribed")
    list_display_links = ("id", "email")
    list_filter = ("id", "email", "is_admin", "is_active", "is_approved",
            "is_subscribed")
    search_fields = ("email",)

    
    db_session_maker = database.AsyncSessionLocal

    async def authenticate(self, username: str, password: str) -> int | None:
        db: Session = database.SessionLocal()
        result = db.execute(text("""select id, email, password from users where email = :email and password = :password and is_admin = true"""), {'email': username, 'password': password})
        result = result.mappings().first()
        if not result:
            return None

        return result.get('id')


@register(models.Animal)
class AnimalAdminModel(CustomAdminModel):
    list_display = ("id", "name", "drugs")
    list_display_links = ("id", "name")
    search_fields = ("name",)

    db_session_maker = database.AsyncSessionLocal


@register(models.Drug)
class DrugAdminModel(CustomAdminModel):
    list_display = ("id","name", "description", "is_global", )
    list_display_links = ("id", "name")
    search_fields = ("name",)
    
    db_session_maker = database.AsyncSessionLocal

