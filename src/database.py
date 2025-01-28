from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, scoped_session
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from src.config import get_settings


engine = create_engine(get_settings().db_url, echo=False, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
Base = declarative_base(bind=engine)

asyncEngine = AsyncEngine(create_engine(get_settings().async_db_url, echo=False))
AsyncSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=asyncEngine, class_=AsyncSession, expire_on_commit=False
)


from src.models.user import User
from src.models.users_payments import UserPayment

def create_tables():
    Base.metadata.create_all(bind=engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
