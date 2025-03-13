from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from src.config import get_settings

conf = ConnectionConfig(
    MAIL_USERNAME=get_settings().mail_username,
    MAIL_PASSWORD=get_settings().mail_password,
    MAIL_FROM=get_settings().mail_from,
    MAIL_PORT=get_settings().mail_port,
    MAIL_SERVER=get_settings().mail_server,
    MAIL_FROM_NAME=get_settings().mail_from_name,
    MAIL_TLS=False,
    MAIL_SSL=True,
    USE_CREDENTIALS=True,
)


async def send_email_async(subject: str, email_to: str, body: str):
    message = MessageSchema(
        recipients=[email_to],
        subject=subject,
        body=body
    )
    fm = FastMail(conf)
    await fm.send_message(message)


async def send_email_password_reset(email: str, code: str):
    await send_email_async("Сброс пароля VetApp", email, f'Ваш код для сброса пароля: {code}')


async def send_email_approve(email: str, code: str):
    await send_email_async("Подтверждение регистрации VetApp", email, f'Ваш код для подтверждения аккаунта: {code}')
