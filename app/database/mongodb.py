import logging
from typing import List, Type

from beanie import Document, init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings

logger = logging.getLogger(__name__)

client: AsyncIOMotorClient = None
database = None


async def connect_to_database():
    global client, database
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    database = client[settings.DATABASE_NAME]
    logger.info(f"Connected to MongoDB: {settings.DATABASE_NAME}")


async def init_beanie_models(document_models: List[Type[Document]]):
    global database
    if database is None:
        await connect_to_database()
    await init_beanie(
        database=database,
        document_models=document_models,
    )
    logger.info(
        f"Beanie initialized with {len(document_models)} models"
    )


async def close_database_connection():
    global client
    if client:
        client.close()
        logger.info("MongoDB connection closed")


def get_database():
    return database
