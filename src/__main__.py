from src import app
import uvicorn
import asyncio
from src.tasks.subscription_checker import check_expired_subscriptions  # Импортируем фоновую задачу

async def start_background_tasks():
    print("🚀 Запускаем фоновую проверку подписок!")  # Проверяем, вызывается ли этот код
    asyncio.create_task(check_expired_subscriptions())

asyncio.run(start_background_tasks()) 

# Запуск FastAPI-сервера
uvicorn.run(
    'src.app:app',
    reload=True,
    host='0.0.0.0',
    workers=1
)
