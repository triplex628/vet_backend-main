from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.database import Base


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    is_active = Column(Boolean, default=True, nullable=False)
    is_approved = Column(Boolean, default=False)
    is_purchased = Column(Boolean, default=False)
    is_subscribed = Column(Boolean, default=False)
    is_subscribed_calc = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    revenuecat_id = Column(String, nullable=True, default=None, index=True)
    uuid_access_token = Column(UUID(as_uuid=True), nullable=True, default=None, index=True)
    last_code = Column(Integer, nullable=True, default=None)
    drugs = relationship('DrugUser', back_populates='user')
    payments = relationship('Payment', back_populates='user')
    user_payments = relationship("UserPayment", back_populates="user", cascade="all, delete-orphan")
    tracking_payments = relationship("PaymentTracking", back_populates="user")
    def __repr__(self):
        return f'User ID:{self.id} Email:{self.email} Active:{self.is_active} Purchased:{self.is_purchased} ' \
               f'Admin:{self.is_admin} '
