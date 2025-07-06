from typing import Sequence
from sqlalchemy.ext.asyncio import async_sessionmaker
from app.chemicals.models import ChemicalOperation, ChemicalObject
from app.chemicals.repository import ChemicalRepository


async def get_source_objects(operation: ChemicalOperation, async_session: async_sessionmaker) -> Sequence[ChemicalObject]:
    async with async_session() as session:
        repo = ChemicalRepository(session)
        return await repo.get_chemical_objects(operation.source_ids)


ChemicalOperation.get_source_objects = get_source_objects
