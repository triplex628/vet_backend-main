from fastapi import APIRouter
from src.handlers import auth, user, drug, animal, payment
from src.handlers.admin_manual import router as admin_manual_router

api_router = APIRouter()
api_router.include_router(auth.router, prefix='/auth', tags=['Auth'])
api_router.include_router(user.router, prefix='/users', tags=['User'])
api_router.include_router(payment.router, prefix='/payments', tags=['Payment'])
api_router.include_router(drug.router, prefix='/drugs', tags=['Drugs'])
api_router.include_router(animal.router, prefix='/animals', tags=['Animals'])


api_router.include_router(admin_manual_router, prefix="/api")

