from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from src.database import get_db
from src.models.manuals import Manual
from src.schemas.manual import ManualCreate, ManualResponse
import os
from uuid import uuid4

router = APIRouter()

UPLOAD_DIR = "static/uploads/admin"
os.makedirs(UPLOAD_DIR, exist_ok=True)  # Создаем папку, если её нет

@router.post("/admin/manuals/download-image")
async def download_manual_image(image_url: str):
    """
    Скачивание изображения по URL и сохранение на сервере.
    """
    try:
        response = requests.get(image_url, stream=True)
        response.raise_for_status()  # Проверяем, что URL доступен

        # Определяем расширение файла
        content_type = response.headers.get("Content-Type", "")
        extension = content_type.split("/")[-1] if "image" in content_type else "jpg"
        
        # Генерируем уникальное имя файла
        unique_filename = f"{uuid4()}.{extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)

        # Сохраняем файл
        with open(file_path, "wb") as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)

        # Возвращаем URL загруженного изображения
        local_image_url = f"/{UPLOAD_DIR}/{unique_filename}"
        return {"image_url": local_image_url}

    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Ошибка при скачивании: {str(e)}")

# Эндпоинт для создания полезного материала
@router.post("/admin/manuals", response_model=ManualResponse)
@router.post("/admin/manuals")
async def create_manual(manual: ManualCreate, db: Session = Depends(get_db)):
    """
    Создание Manual, скачивая изображение перед сохранением, если передан URL.
    """
    if manual.image_url.startswith("http"):
        image_data = await download_manual_image(manual.image_url)
        manual.image_url = image_data["image_url"]

    new_manual = Manual(
        title=manual.title,
        description=manual.description,
        image_url=manual.image_url
    )

    db.add(new_manual)
    db.commit()
    db.refresh(new_manual)
    return new_manual

