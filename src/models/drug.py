from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, Table
from sqlalchemy.orm import relationship

from src.database import Base

drugs_animals_association = Table('drugs_animals', Base.metadata,
                                  Column('drug', ForeignKey('drugs.id'), primary_key=True),
                                  Column('animal', ForeignKey('animals.id'), primary_key=True)
                                  )

class DrugUser(Base):
    __tablename__ = 'drugs_users'
    drug_id = Column(ForeignKey('drugs.id'), primary_key=True)
    user_id = Column(ForeignKey('users.id'), primary_key=True)
    is_favorite = Column(Boolean, default=False, nullable=False)
    drug = relationship('Drug', back_populates='users')
    user = relationship('User', back_populates='drugs')


class Drug(Base):
    __tablename__ = 'drugs'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_global = Column(Boolean, default=False, nullable=False)
    animals = relationship('Animal', secondary=drugs_animals_association, back_populates='drugs')
    users = relationship('DrugUser', back_populates='drug')

    def __repr__(self):
        return f'Drug ID:{self.id} Name:{self.name} Global:{self.is_global}'