from pydantic import BaseModel
from typing import List, Optional
from pydantic import BaseModel

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

class SubscriptionStatus(BaseModel):
    active: bool
    expires: Optional[str]
    type: Optional[str]

class PaymentResponse(BaseModel):
    payment_url: str
    success_url: str
    failure_url: str


class CancelSubscriptionRequest(BaseModel):
    user_id: int
