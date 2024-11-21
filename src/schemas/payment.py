from pydantic import BaseModel

class PromadusPaymentInfo(BaseModel):
    order_id: str
    payment_status: str
    payment_status_description: str
