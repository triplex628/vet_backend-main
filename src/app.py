from src.database import create_tables, SessionLocal
from src.models import user, drug, manuals
from fastapi import FastAPI
from src.handlers import api_router
from fastadmin import fastapi_app as admin_app
from src import admin
from src.handlers.subscription import router as subscription_router


create_tables()

app = FastAPI()
app.include_router(api_router)
app.include_router(subscription_router)

app.mount("/admin", admin_app)
