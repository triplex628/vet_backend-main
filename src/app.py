from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy.engine import Engine
from sqlalchemy import event
from sqlalchemy.exc import SQLAlchemyError
import logging
import json
import traceback

from src.database import create_tables, SessionLocal
from src.models import user, drug, manuals
from src.handlers import api_router
from fastadmin import fastapi_app as admin_app
from src import admin
from src.handlers.subscription import router as subscription_router
from src.handlers.revenue import router as revenuecat_router 
from src.handlers import admin_manual 
from src.handlers.admin_manual import router as admin_manual_router
logging.basicConfig(level=logging.DEBUG)

#Логирование SQL-запросов
@event.listens_for(Engine, "before_execute")
def log_sql(conn, clauseelement, multiparams, params):
    logging.debug(f"Executing SQL: {str(clauseelement)}")
    logging.debug(f"With params: {params}")

create_tables()

app = FastAPI()

#Исправляем payload перед отправкой в FastAdmin
@app.middleware("http")
async def fix_payload_middleware(request: Request, call_next):
    """Middleware для исправления payload перед отправкой в FastAdmin"""
    
    if request.method in ["PATCH"]:
        try:
            body = await request.body()
            if body:
                payload = json.loads(body.decode("utf-8"))

                # Если в payload есть animals, исправляем их
                if "animals" in payload and isinstance(payload["animals"], list):
                    fixed_animals = []
                    for item in payload["animals"]:
                        if isinstance(item, str):  
                            fixed_animals.extend([int(x) for x in item.split(",") if x.isdigit()])
                        elif isinstance(item, int):
                            fixed_animals.append(item)
                    
                    payload["animals"] = fixed_animals

                print(f"Fixed payload before sending to FastAdmin: {payload}")

                # Перезаписываем тело запроса
                async def receive():
                    return {"type": "http.request", "body": json.dumps(payload).encode("utf-8")}

                request = Request(scope=request.scope, receive=receive)

        except Exception as e:
            print(f"Error in payload middleware: {e}")

    response = await call_next(request)
    return response


app.include_router(api_router)
app.include_router(subscription_router)
app.include_router(revenuecat_router)
app.include_router(admin_manual_router)
app.mount("/admin", admin_app)


# Подключаем папку static для отображения изображений
app.mount("/static", StaticFiles(directory="static"), name="static")
