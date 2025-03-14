from fastapi import APIRouter, BackgroundTasks
from src.utils.email import send_email_async

router = APIRouter()

@router.post("/send-test-email/")
async def send_test_email(background_tasks: BackgroundTasks):
    """Тест отправки письма"""
    background_tasks.add_task(
        send_email_async, "Тестовое письмо", "lololosha579@gmail.com", "Привет, это тест!"
    )
    return {"message": "Email отправлен"}
