from pydantic import BaseModel
from typing import Optional

class ManualBase(BaseModel):
    title: str
    description: Optional[str]

class ManualCreate(ManualBase):
    image_url: Optional[str]

class ManualResponse(ManualBase):
    id: int
    image_url: Optional[str]

    class Config:
        orm_mode = True
