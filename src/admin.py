from typing import Any
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastadmin import SqlAlchemyModelAdmin, register
import requests
from sqlalchemy import text
from src import models
from src import database
import os
import uuid
from uuid import uuid4 

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



UPLOAD_DIR = "static/uploads/admin"
os.makedirs(UPLOAD_DIR, exist_ok=True)  # Убедимся, что папка существует

router = APIRouter()


def download_image_from_url(image_url: str) -> str:
    """
    Скачивает изображение по URL и сохраняет на сервере.
    """
    print(f"Скачиваю изображение: {image_url}")  
    
    try:
        response = requests.get(image_url, stream=True)
        response.raise_for_status()

        # Проверяем, является ли контент изображением
        content_type = response.headers.get("Content-Type", "")
        if not content_type.startswith("image/"):
            print(f"Ошибка: Ссылка не ведет на изображение! Content-Type: {content_type}")
            return image_url  # Просто оставляем URL, если это не изображение

        # Определяем расширение
        extension = content_type.split("/")[-1] if "image" in content_type else "jpg"

        unique_filename = f"{uuid4()}.{extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)

        # Сохраняем изображение
        with open(file_path, "wb") as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)

        print(f"Изображение сохранено: {file_path}")
        return f"/{UPLOAD_DIR}/{unique_filename}"  

    except requests.RequestException as e:
        print(f"Ошибка загрузки: {e}")
        return image_url



@register(models.Manual)
class ManualAdminModel(SqlAlchemyModelAdmin):
    list_display = ("id", "title", "description", "image_url")
    list_display_links = ("id", "title")
    search_fields = ("title",)
    form_fields = {
        "title": "text",
        "description": "textarea",
        "image_url": "text",  
    }

    db_session_maker = database.AsyncSessionLocal

    async def orm_save_obj(self, id: int, payload: dict):
        """
        Перед сохранением скачивает изображение по URL, если необходимо.
        """
        print(f" Сохранение объекта: {payload}")  
        
        if "image_url" in payload and payload["image_url"].startswith("http"):
            print(f"Найден URL изображения: {payload['image_url']}")  
            payload["image_url"] = download_image_from_url(payload["image_url"])
        
        return await super().orm_save_obj(id, payload)
    
    async def orm_delete_obj(self, id: int):
        """
        Удаляет объект из базы данных.
        """
        print(f"Пытаюсь удалить запись с ID: {id}") 

        sessionmaker = self.get_sessionmaker()
        async with sessionmaker() as session:
            obj = await session.get(self.model_cls, id)
            if obj:
                await session.delete(obj)
                await session.commit()
                print(f"Запись {id} удалена из базы!")
            else:
                print(f"Запись {id} не найдена в БД!")



@router.post("/admin/manuals/upload", tags=["Admin"])
async def admin_upload_manual_image(file: UploadFile = File(...)):
    """
    Эндпоинт для загрузки изображений из админ-панели.
    """
    file_name = f"{uuid.uuid4()}.{file.filename.split('.')[-1]}"
    file_path = f"static/uploads/admin/{file_name}"

    os.makedirs("static/uploads/admin", exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(file.file.read())

    return {"file_path": f"/static/uploads/admin/{file_name}"}
