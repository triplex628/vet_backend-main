import base64
import uuid
from fastapi import HTTPException
import requests

class YookassaService:
    def __init__(self):
        self.shop_id = "906463"
        self.api_key = "live_0C5t-v3_osoqHKsF1GOSrhWfXyoxwVdIgvA-T_P2iC0"
        self.base_url = "https://api.yookassa.ru/v3"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Basic " + base64.b64encode(f"{self.shop_id}:{self.api_key}".encode()).decode(),
            "Idempotence-Key": str(uuid.uuid4())
        }

    def create_payment(self, price: int, return_url: str) -> dict:
        """
        Создает платеж через Юкассу
        """
        payload = {
            "amount": {"value": f"{price}", "currency": "RUB"},
            "payment_method_data": {"type": "bank_card"},
            "confirmation": {"type": "redirect", "return_url": return_url},
            "description": "Полная версия Vet App"
        }

        try:
            response = requests.post(
                f"{self.base_url}/payments",
                json=payload,
                headers=self.headers
            )
            # print("Request payload:", payload)  
            # print("Response status:", response.status_code)  
            # print("Response text:", response.text)  
            
            response.raise_for_status()
            data = response.json()
            return {
                "confirmation_url": data["confirmation"]["confirmation_url"],
                "payment_id": data["id"]
            }
        except requests.RequestException as e:
            print(f"Error creating Yookassa payment: {e}")
            raise HTTPException(status_code=500, detail="Error creating payment with Yookassa")

    def __init__(self):
        self.shop_id = "906463"
        self.api_key = "live_0C5t-v3_osoqHKsF1GOSrhWfXyoxwVdIgvA-T_P2iC0"
        self.base_url = "https://api.yookassa.ru/v3"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Basic " + base64.b64encode(f"{self.shop_id}:{self.api_key}".encode()).decode(),
            "Idempotence-Key": str(uuid.uuid4())
        }

    def check_yookassa_payment(self, ticket_id: str) -> dict:
        """
        Проверяет статус платежа в Yookassa по ticket_id.
        """
        try:
            response = requests.get(f"{self.base_url}/payments/{ticket_id}", headers=self.headers)
            response_data = response.json()
            print("Parsed Yookassa response:", response_data)
            return response_data
        except Exception as e:
            print("Error checking Yookassa payment:", e)
            return {}

