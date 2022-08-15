from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from ocrd_webapi.models import WorkspaceDb


async def initiate_database(db_url: str):
    client = AsyncIOMotorClient(db_url)
    await init_beanie(
        database=client.get_default_database(default='operandi'),
        document_models=[WorkspaceDb]
    )
