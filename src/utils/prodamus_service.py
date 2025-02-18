import requests
from typing import Optional


class ProdamusService:
    BASE_URL = "https://vetapp.payform.ru"

    @staticmethod
    def generate_payment_link(order_id: str, email: str, description: str, price: int) -> Optional[str]:
        """
        Генерация ссылки для оплаты через Prodamus.

        :param order_id: Уникальный идентификатор заказа.
        :param email: Email пользователя.
        :param description: Описание покупки.
        :param price: Цена заказа в рублях.
        :return: Ссылка на оплату или None, если запрос не удался.
        """
        payload = {
            "do": "link",
            "order_id": order_id,
            "customer_email": email,
            "paid_content": description,
            "products[0][name]": description,
            "products[0][quantity]": 1,
            "products[0][price]": price,
        }

        try:
            response = requests.get(ProdamusService.BASE_URL, params=payload)
            if response.status_code == 200:
                return response.text  
            else:
                print(f"Error from Prodamus: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Exception during Prodamus payment generation: {e}")
            return None


    def check_prodamus_payment(ticket_id: str):
            url = f"https://vetapp.payform.ru/api/v1/payment/{ticket_id}"  
            headers = {
                "Authorization": "Basic your_api_key",
                "Content-Type": "application/json"
            }

            try:
                response = requests.get(url, headers=headers)
                print(f"Prodamus response status: {response.status_code}")
                print(f"Prodamus response text: {response.text}")  

                if response.status_code != 200:
                    return {"error": f"Unexpected status code {response.status_code}"}

                return response.json()  

            except requests.exceptions.RequestException as e:
                print(f"Request error: {e}")
                return {"error": "Failed to connect to Prodamus"}

