from sqlalchemy import Column, Integer, String
from src.database import Base

class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

    def __str__(self):
        return self.name 