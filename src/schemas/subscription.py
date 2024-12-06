from pydantic import BaseModel
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class PurchaseResponse(BaseModel):
    payment_url: str
    return_url: str

class SubscriptionOption(BaseModel):
    type: str
    price: int
    title: str

class SubscriptionResponse(BaseModel):
    subscriptions: List[SubscriptionOption]

class SubscriptionRequest(BaseModel):
    user_id: int
    type: str
    payment_method: str

class SubscriptionStatus(BaseModel):
    active: bool
    expires: Optional[str]
    type: Optional[str]

class PaymentResponse(BaseModel):
    payment_url: str
    success_url: str
    failure_url: str
    ticket_id: str


class CancelSubscriptionRequest(BaseModel):
    user_id: int


class PaymentSuccessRequest(BaseModel):
    ticket_id: str

class PaymentSuccessResponse(BaseModel):
    detail: str
    subscription_type: str
    expiration_date: Optional[datetime] 