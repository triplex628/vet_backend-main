from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from src.database import Base
from src.models.drug import drugs_animals_association


class Animal(Base):
    __tablename__ = "animals"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    drugs = relationship('Drug', secondary=drugs_animals_association, back_populates='animals')

    def __repr__(self):
        return f'Animal ID:{self.id} Name:{self.name}'



class Manual(Base):
    __tablename__ = "manuals"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    image_url = Column(String, nullable=True)  
