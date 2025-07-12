from dataclasses import dataclass
from typing import Dict, Any

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.chemicals.repository import ChemicalRepository, ChemicalObjectExistsException, ChemicalOperationException
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

    async def add_chemical_with_composition(
            self,
            admin_login: str,
            composition_data: ChemicalCompositionSchema
    ) -> Dict[str, Any]:
        admin_role = await self.user_repository.get_user_role(admin_login)
        if admin_role != "admin":
            raise AdminRequiredException("Only admin can create users")

        chemical_object = await self.chemical_repository.get_chemical_object_by_formula(composition_data.formula)
        if not chemical_object:
            raise HTTPException(
                status_code=404,
                detail=f"Chemical object with formula {composition_data.formula} not found"
            )

        if not chemical_object.source_check:
            raise HTTPException(
                status_code=400,
                detail=f"Chemical object {composition_data.formula} is not marked as source (source_check is False)"
            )

        result = await self.chemical_repository.add_percent_composition(
            type_id=chemical_object.id,
            composition=composition_data.metal_composition
        )
        return result

    async def delete_chemical_composition(
            self,
            admin_login: str,
            delete_data: MetalCompositionDelete
    ) -> Dict[str, Any]:
        admin_role = await self.user_repository.get_user_role(admin_login)
        if admin_role != "admin":
            raise AdminRequiredException("Only admin can delete compositions")

        result = await self.chemical_repository.delete_percent_composition(delete_data)
        return result

    async def create_chemical_operation(
            self,
            admin_login: str,
            operation_data: OperationsSchema
    ) -> Dict[str, Any]:

        admin_role = await self.user_repository.get_user_role(admin_login)
        if admin_role != "admin":
            raise AdminRequiredException("Only admin can create users")

        target_object = await self.chemical_repository.get_chemical_object_by_formula(operation_data.target)

        if not target_object:
            raise HTTPException(
                status_code=404,
                detail=f"Target chemical object with {operation_data.target} not found"
            )

        await self.chemical_repository.validate_source_objects(operation_data.source)

        try:
            operation = await self.chemical_repository.create_chemical_operation(operation_data)
            return {
                "message": "Chemical operation created successfully",
                "operation_id": operation.id,
                "target_id": operation.target_id,
                "source_ids": operation.source_ids
            }

        except ChemicalOperationException as e:
            raise HTTPException(
                status_code=400,
                detail=str(e)
            )

        except IntegrityError as e:
            await self.chemical_repository.db_session.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Database integrity error: {str(e.orig)}"
            )

        except Exception as e:
            await self.chemical_repository.db_session.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Internal server error: {str(e)}"
            )

    async def delete_chemical_operation(
        self,
        admin_login: str,
        target_formula: str,
        source_formula: str
    ) -> Dict[str, str]:
        admin_role = await self.user_repository.get_user_role(admin_login)
        if admin_role != "admin":
            raise AdminRequiredException("Only admin can delete operations")

        await self.chemical_repository.delete_chemical_operation(target_formula, source_formula)
        return {"message": f"Chemical operation with target {target_formula} and source {source_formula} deleted successfully"}
