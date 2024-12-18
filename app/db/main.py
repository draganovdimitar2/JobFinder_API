from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from app.config import Config


engine = create_async_engine(url = Config.DATABASE_URL)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)  # conn is our connection object. we want to access the metadata object on top of this SQLModel

        # function to return our session

async def get_session() -> AsyncSession:
    async_session = async_sessionmaker(  # we have to bond it with our AsyncEngine to carry out our CRUD
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False  # every session can be used after commiting
    )

    async with async_session() as session:
        yield session
