from datetime import datetime, timedelta
from enum import Enum
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.database import Base

class SubscriptionType(Enum):
    MONTHLY = ("monthly", "Ежемесячная подписка", 199)
    HALF_YEARLY = ("half_yearly", "Полугодовая подписка", 949)
    YEARLY = ("yearly", "Годовая подписка", 1549)
    LIFETIME = ("lifetime", "Пожизненная подписка", 9999999)
    CALCULATOR_MONTH = ("calculator_month", "Месячная подписка на калькулятор", 99)
    CALCULATOR_YEAR = ("calculator_year", "Годовая подписка на калькулятор", 849)

    def __init__(self, value, title, price):
        self._value_ = value
        self.title = title
        self.price = price

    @property
    def get_price(self):
        return self.price

class Payment(Base):
    __tablename__ = 'users_payments'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship('User', back_populates='payments')
    ticket_id = Column(UUID(as_uuid=True), nullable=True, default=None, index=True)
    payment_system = Column(String, default='prodamus')
    subscription_type = Column(SQLAlchemyEnum(SubscriptionType), nullable=True)
    expiration_date = Column(DateTime, nullable=True)

    def set_expiration_date(self):
        if self.subscription_type == SubscriptionType.MONTHLY or self.subscription_type == SubscriptionType.CALCULATOR_MONTH:
            self.expiration_date = datetime.utcnow() + timedelta(days=30)
        elif self.subscription_type == SubscriptionType.HALF_YEARLY:
            self.expiration_date = datetime.utcnow() + timedelta(days=182)
        elif self.subscription_type == SubscriptionType.YEARLY or self.subscription_type == SubscriptionType.CALCULATOR_YEAR:
            self.expiration_date = datetime.utcnow() + timedelta(days=365)

    def __repr__(self):
        return (f'Payment ID: {self.id}, User ID: {self.user_id}, '
                f'Subscription Type: {self.subscription_type}, '
                f'Expires: {self.expiration_date}')



class PaymentTracking(Base):
    __tablename__ = "payment_tracking"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ticket_id = Column(UUID(as_uuid=True), nullable=False)
    subscription_type = Column(String, nullable=False)
    payment_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="tracking_payments")