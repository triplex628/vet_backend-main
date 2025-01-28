from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from src.database import Base

class UserPayment(Base):
    __tablename__ = "users_payments"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    ticket_id = Column(String, nullable=True, index=True)
    payment_system = Column(String, nullable=False)
    subscription_type = Column(String, nullable=False)  
    expiration_date = Column(DateTime, nullable=False)

    user = relationship("User", back_populates="user_payments")
