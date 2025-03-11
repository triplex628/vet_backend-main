from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, Table
from sqlalchemy.orm import relationship

from src.database import Base
from src.models.drug import drugs_animals_association
from src.models.groups import Group

manuals_animals_association = Table(
    "manuals_animals",
    Base.metadata,
    Column("manual_id", Integer, ForeignKey("manuals.id", ondelete="CASCADE"), primary_key=True),
    Column("animal_id", Integer, ForeignKey("animals.id", ondelete="CASCADE"), primary_key=True),
)

class Animal(Base):
    __tablename__ = "animals"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    drugs = relationship('Drug', secondary=drugs_animals_association, back_populates='animals')
    manuals = relationship("Manual", secondary=manuals_animals_association, back_populates="animals")

    def __repr__(self):
        return f'Animal ID:{self.id} Name:{self.name}'



class Manual(Base):
    __tablename__ = "manuals"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    image_url = Column(String, nullable=True)  
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)  # 👈 Делаем внешним ключом
    group = relationship("Group", backref="manuals")
    animals = relationship("Animal", secondary=manuals_animals_association, back_populates="manuals")
    
