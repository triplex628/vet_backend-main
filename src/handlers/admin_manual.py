from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
import requests
from sqlalchemy.orm import Session
from src.database import get_db
from src.models.manuals import Manual
from src.schemas.manual import ManualCreate, ManualResponse
import os
from uuid import uuid4
from typing import Dict, List, Optional
from collections import defaultdict
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.models.groups import Group


router = APIRouter()

UPLOAD_DIR = "static/uploads/admin"
os.makedirs(UPLOAD_DIR, exist_ok=True)  

@router.post("/admin/manuals/download-image")
async def download_manual_image(image_url: str):
    """
    Скачивание изображения по URL и сохранение на сервере.
    """
    try:
        response = requests.get(image_url, stream=True)
        response.raise_for_status()  

       
        content_type = response.headers.get("Content-Type", "")
        extension = content_type.split("/")[-1] if "image" in content_type else "jpg"
        
        
        unique_filename = f"{uuid4()}.{extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)

       
        with open(file_path, "wb") as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)

        
        local_image_url = f"/{UPLOAD_DIR}/{unique_filename}"
        return {"image_url": local_image_url}

    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Ошибка при скачивании: {str(e)}")


@router.post("/admin/manuals", response_model=ManualResponse)
async def create_manual(manual: ManualCreate, db: Session = Depends(get_db)):
    """
    Создание Manual, скачивая изображение перед сохранением, если передан URL.
    """
    if manual.image_url.startswith("http"):
        image_data = await download_manual_image(manual.image_url)
        manual.image_url = image_data["image_url"]

    new_manual = Manual(
        name=manual.name,
        description=manual.description,
        image_url=manual.image_url
    )

    db.add(new_manual)
    db.commit()
    db.refresh(new_manual)
    return new_manual

from collections import defaultdict

@router.get("/manuals")
def get_manuals(db: Session = Depends(get_db)):
    """Возвращает список manuals, сгруппированных по group_name"""
    
    # Загружаем все группы один раз
    groups = db.query(Group).all()
    group_emojis = {group.name: group.emoji for group in groups}

    # Загружаем все manuals
    manuals = db.query(Manual).order_by(Manual.id).all()

    grouped_manuals: Dict[str, Dict] = {}

    for manual in manuals:
        group_name = manual.group_name
        group_emoji = group_emojis.get(group_name, "")

        if group_name not in grouped_manuals:
            grouped_manuals[group_name] = {
                "group_name": group_name,
                "emoji_group": group_emoji,
                "items": []
            }

        grouped_manuals[group_name]["items"].append({
            "id": manual.id,
            "name": manual.name,
            "description": manual.description,
            "imageUrl": manual.image_url,
            "animals": [{"id": animal.id, "name": animal.name} for animal in manual.animals],
            "emoji": manual.emoji
        })

    return list(grouped_manuals.values())



@router.get("/manuals/group/{group_id}")
def get_manuals_by_group(group_id: int, db: Session = Depends(get_db)):
    """Получает записи только из указанной группы"""
    manuals = db.query(Manual).filter(Manual.group_id == group_id).all()

    return [
        {
            "id": manual.id,
            "name": manual.name,
            "description": manual.description,
            "imageUrl": manual.image_url,
            "animals": [{"id": animal.id, "name": animal.name} for animal in manual.animals]
        }
        for manual in manuals
    ]


class GroupResponse(BaseModel):
    id: int
    name: str

@router.get("/groups", response_model=List[GroupResponse])
def get_groups(db: Session = Depends(get_db)):  

    groups = db.query(Group).order_by(Group.id).all()  

    return [{"id": g.id, "name": g.name} for g in groups]

@router.get("/manuals/search", response_model=List[ManualResponse])
def search_manuals(query: Optional[str] = None, db: Session = Depends(get_db)):

    stmt = select(Manual).order_by(Manual.id)
    if query:
        stmt = stmt.filter(Manual.name.ilike(f"%{query}%"))

    manuals = db.execute(stmt).scalars().all()


    response = []
    for manual in manuals:
        response.append({
            "id": manual.id,
            "name": manual.name, 
            "description": manual.description,
            "imageUrl": manual.image_url,
            "group_id": manual.group_id,
            "animals": [{"id": animal.id, "name": animal.name} for animal in manual.animals]  
        })

    return response