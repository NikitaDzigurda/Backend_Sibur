from dataclasses import dataclass

from app.chemicals import ChemicalRepository
from app.chemicals.schema import *


@dataclass
class UserChemicalService:
    chemical_repository: ChemicalRepository

    async def get_all_target_chemical_objects(
            self
    ) -> List[str]:
        return await self.chemical_repository.get_all_target_chemical_objects()
