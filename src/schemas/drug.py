from pydantic import BaseModel
from typing import Optional

from .animal import Animal


class DrugBase(BaseModel):
    name: str
    description: Optional[str] = None
    animals: Optional[list[Animal]] = None
    is_favorite: bool = False


class Drug(DrugBase):
    id: int

    class Config:
        orm_mode = True


class DrugCreate(DrugBase):
    animals: Optional[list[int]] = None


# исключить is_favorite
class DrugPatchUpdate(DrugBase):
    name: Optional[str] = None
    animals: Optional[list[int]] = None
