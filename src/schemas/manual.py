from pydantic import BaseModel
from typing import List, Optional

class ManualBase(BaseModel):
    name: str
    description: Optional[str]

class ManualCreate(ManualBase):
    name: str
    description: Optional[str]
    imageUrl: Optional[str]
    group_name: Optional[str]
    animals: List[int] 

class AnimalResponse(BaseModel):
    id: int
    name: str
    
class ManualResponse(ManualBase):
    id: int
    name: str
    description: Optional[str]
    imageUrl: Optional[str]
    group_id: Optional[int]
    group_name: Optional[str]
    animals: List[AnimalResponse]

    class Config:
        orm_mode = True

