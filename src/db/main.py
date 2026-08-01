from sqlmodel import create_engine,text
from sqlalchemy.ext.asyncio import create_async_engine,AsyncEngine
from src.config import Config
from sqlmodel import SQLModel
from .models import Dataset

print("Imported Dataset:", Dataset)
print("Dataset table:", Dataset.__table__)
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker
import ssl
from sqlalchemy.pool import NullPool
ssl_context = ssl.create_default_context()
# engine = create_async_engine(
#     Config.DATABASE_URL,
#     connect_args={"ssl": ssl_context},
#     echo=True
# )
engine = create_async_engine(
    Config.DATABASE_URL,
    connect_args={"ssl": ssl_context},
    pool_pre_ping=True,
    poolclass=NullPool,
)

async def initdb():
    """creatte a connection to our db"""
    
    print("Registered tables:", SQLModel.metadata.tables.keys())
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_session():
    async with AsyncSessionLocal() as session:
        yield session