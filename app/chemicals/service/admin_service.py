from dataclasses import dataclass
from typing import Dict, Any

from fastapi import HTTPException

from app.infrastructure import Base
from app.chemicals.repository import ChemicalRepository, ChemicalObjectExistsException
from app.users.user_profile.admin.repository import UserRepository, AdminRequiredException
from app.chemicals.schema import *
from app.chemicals.models import *


@dataclass
class AdminChemicalService:
    chemical_repository: ChemicalRepository
    user_repository: UserRepository

    async def get_table_data(
            self,
            model: Base,
            admin_login: str
    ) -> Dict[str, Any]:

        admin_role = await self.user_repository.get_user_role(admin_login)
        if admin_role != "admin":
            raise AdminRequiredException("Only admin can create users")

        try:
            return await self.chemical_repository.get_full_table_contents(model)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch table data: {str(e)}"
            )

    async def get_all_tables(
            self,
            admin_login: str

    ):
        admin_role = await self.user_repository.get_user_role(admin_login)
        if admin_role != "admin":
            raise AdminRequiredException("Only admin can create users")

        tables = await self.chemical_repository.get_all_tables()
        filtered_tables = [table for table in tables["tables"] if table != "alembic_version"]
        return {"tables": filtered_tables}

    async def create_chemical_object(
            self,
            admin_login: str,
            new_chemical_object: RawMaterialSchema
    ) -> ChemicalObject:
        admin_role = await self.user_repository.get_user_role(admin_login)
        if admin_role != "admin":
            raise AdminRequiredException("Only admin can create users")

        if await self.chemical_repository.test(new_chemical_object.formula) is not None:
            raise ChemicalObjectExistsException(f"Chemical material {new_chemical_object.formula} already exists")

        return await self.chemical_repository.create_chemical_objects(new_chemical_object)

    async def delete_chemical_object(
            self,
            chemical_object: str,
            admin_login: str
    ):
        admin_role = await self.user_repository.get_user_role(admin_login)
        if admin_role != "admin":
            raise AdminRequiredException("Only admin can create users")

        object_id = await self.chemical_repository.get_id_by_formula(chemical_object)
        if not object_id:
            raise HTTPException(status_code=404, detail=f"Chemical object {chemical_object} not found")

        await self.chemical_repository.delete_object_and_dependencies(object_id)



