from dataclasses import dataclass
from fastapi import HTTPException
from typing import Sequence, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, text, insert, update, func, delete


from app.chemicals.models import ChemicalObject, ChemicalOperation, PercentChemicalElements
from app.infrastructure import Base
from app.chemicals.schema import *

import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


class ChemicalObjectExistsException(Exception):
    pass


class ChemicalOperationException(Exception):
    pass


@dataclass
class ChemicalRepository:
    db_session: AsyncSession

    async def get_all_target_chemical_objects(self):
        result = await self.db_session.execute(
            select(ChemicalObject.chemical_formula).where(ChemicalObject.source_check.is_(False)))
        return result.scalars().all()

    async def get_chemical_object_by_formula(self, formula: str) -> Optional[ChemicalObject]:
        result = await self.db_session.execute(
            select(ChemicalObject).where(ChemicalObject.chemical_formula == formula)
        )
        return result.scalar_one_or_none()

    async def get_chemical_objects(self, ids: List[int]) -> Sequence[ChemicalObject]:
        result = await self.db_session.execute(
            select(ChemicalObject).where(ChemicalObject.id.in_(ids)))
        ids = result.scalars().all()
        return list(ids) if isinstance(ids, list) else [ids]

    async def get_operation(self, object_id: int) -> Optional[ChemicalOperation]:
        result = await self.db_session.execute(
            select(ChemicalOperation).where(ChemicalOperation.id == object_id))
        return result.scalar_one_or_none()

    async def get_id_by_formula(self, formula: str) -> int:
        print(f"Checking formula in DB: {formula}")
        result = await self.db_session.execute(
            select(ChemicalObject.id)
            .where(ChemicalObject.chemical_formula == formula)
        )
        found_id = result.scalar_one_or_none()
        print(f"Found ID: {found_id}")
        return found_id

    async def get_id_by_formula_normalized(self, formula: str) -> int:
        print(f"Checking formula in DB: {formula}")
        normalized_formula = formula.replace('{', '').replace('}', '')
        result = await self.db_session.execute(
            select(ChemicalObject.id)
            .where(ChemicalObject.chemical_formula == normalized_formula)
        )
        found_id = result.scalar_one_or_none()
        print(f"Found ID: {found_id}")
        return found_id

    async def test(self, formula: str) -> int:
        print(f"Checking formula in DB: {formula}")
        result = await self.db_session.execute(
            select(ChemicalObject.chemical_formula)
            .where(ChemicalObject.chemical_formula == formula)
        )
        found_formula = result.scalar_one_or_none()
        print(f"Found ID: {found_formula}")
        return found_formula

    async def get_chemical_object_by_id(self, object_id: int) -> Optional[ChemicalObject]:
        result = await self.db_session.execute(
            select(ChemicalObject).where(ChemicalObject.id == object_id)
        )
        return result.scalar_one_or_none()

    async def validate_source_objects(self, source_ids: List[int]) -> None:
        for source_id in source_ids:
            source_object = await self.get_chemical_object_by_id(source_id)
            if not source_object:
                raise HTTPException(
                    status_code=404,
                    detail=f"Source chemical object with ID {source_id} not found"
                )

    async def get_source_formulas_by_target_id(self, target_id: int) -> Sequence[str]:
        result = await self.db_session.execute(
            select(ChemicalOperation.source_ids).where(ChemicalOperation.target_id == target_id)
        )
        source_id_lists = result.scalars().all()

        unique_source_ids = list({source_id for ids in source_id_lists for source_id in ids})

        if not unique_source_ids:
            return []

        result = await self.db_session.execute(
            select(ChemicalObject.chemical_formula).where(ChemicalObject.id.in_(unique_source_ids))
        )
        return result.scalars().all()

    async def get_full_table_contents(self, model: Base) -> Dict[str, Any]:

        columns = list(model.__table__.columns.keys())

        result = await self.db_session.execute(select(model))
        rows = result.scalars().all()

        data = [
            {col: getattr(row, col) for col in columns}
            for row in rows
        ]

        return {
            "columns": columns,
            "data": data,
            "count": len(data)
        }

    async def get_all_tables(self):
        result = await self.db_session.execute(
            text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
        )
        tables = [row[0] for row in result]
        return {"tables": tables}

    async def create_chemical_objects(self, chemical_data: RawMaterialSchema) -> ChemicalObject:
        try:
            result = await self.db_session.execute(
                insert(ChemicalObject).values(
                    chemical_formula=chemical_data.formula,
                    source_check=chemical_data.source_check,
                    molar_mass=chemical_data.molar_mass
                ).returning(ChemicalObject)
            )
            await self.db_session.commit()
            return result.scalar_one()

        except IntegrityError as e:
            print("IntegrityError raised during INSERT:", e.orig)
            await self.db_session.rollback()
            raise ChemicalObjectExistsException(f"Chemical material {chemical_data.formula} already exists")

    async def delete_object_and_dependencies(self, object_id: int) -> None:
        await self.db_session.execute(
            update(ChemicalOperation)
            .where(ChemicalOperation.source_ids.any(object_id))
            .values(
                source_ids=func.array_remove(ChemicalOperation.source_ids, object_id)
            )
        )
        await self.db_session.execute(
            delete(ChemicalOperation).where(func.cardinality(ChemicalOperation.source_ids) == 0)
        )
        await self.db_session.execute(
            delete(ChemicalObject).where(ChemicalObject.id == object_id)
        )

        await self.db_session.commit()

    async def get_percent_composition_by_type_id(self, type_id: int) -> Sequence[PercentChemicalElements]:
        result = await self.db_session.execute(
            select(PercentChemicalElements).where(PercentChemicalElements.type_id == type_id)
        )
        return result.scalars().all()

    async def add_percent_composition(self, type_id: int, composition: MetalComposition) -> Dict[str, str]:
        existing_records = await self.get_percent_composition_by_type_id(type_id)

        if existing_records:
            for record in existing_records:
                if (record.main_percent == composition.main_percent and
                        record.Fe_percent == composition.Fe_percent and
                        record.Si_percent == composition.Si_percent and
                        record.K_percent == composition.K_percent and
                        record.Ca_percent == composition.Ca_percent and
                        record.Mg_percent == composition.Mg_percent and
                        record.Na_percent == composition.Na_percent):
                    return {"message": f"Composition for type_id {type_id} already exists with these characteristics"}

        try:
            stmt = insert(PercentChemicalElements).values(
                type_id=type_id,
                main_percent=composition.main_percent,
                Fe_percent=composition.Fe_percent,
                Si_percent=composition.Si_percent,
                K_percent=composition.K_percent,
                Ca_percent=composition.Ca_percent,
                Mg_percent=composition.Mg_percent,
                Na_percent=composition.Na_percent
            )
            await self.db_session.execute(stmt)
            await self.db_session.commit()
            return {"message": f"New composition added for type_id {type_id} successfully"}
        except IntegrityError as e:
            await self.db_session.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to add new composition for type_id {type_id}: {str(e)}"
            )

    async def delete_percent_composition(self, delete_data: MetalCompositionDelete) -> Dict[str, str]:
        chemical_object = await self.get_chemical_object_by_formula(delete_data.chemical_formula)
        if not chemical_object:
            raise HTTPException(
                status_code=404,
                detail=f"Chemical object with formula {delete_data.chemical_formula} not found"
            )

        type_id = chemical_object.id
        delete_stmt = (
            delete(PercentChemicalElements)
            .where(PercentChemicalElements.type_id == type_id)
            .where(PercentChemicalElements.main_percent == delete_data.main_percent)
            .where(PercentChemicalElements.Fe_percent == delete_data.Fe_percent)
            .where(PercentChemicalElements.Si_percent == delete_data.Si_percent)
            .where(PercentChemicalElements.K_percent == delete_data.K_percent)
            .where(PercentChemicalElements.Ca_percent == delete_data.Ca_percent)
            .where(PercentChemicalElements.Mg_percent == delete_data.Mg_percent)
            .where(PercentChemicalElements.Na_percent == delete_data.Na_percent)
        )

        result = await self.db_session.execute(delete_stmt)
        if result.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail=f"No composition found for type_id {type_id} with given parameters"
            )

        await self.db_session.commit()
        return {"message": f"Composition for type_id {type_id} deleted successfully"}

    async def create_chemical_operation(self, operation_data: OperationsSchema) -> ChemicalOperation:
        target_id = await self.get_id_by_formula(operation_data.target)

        result = await self.db_session.execute(
            select(ChemicalOperation)
            .where(ChemicalOperation.source_ids == operation_data.source)
            .where(ChemicalOperation.target_id == target_id)
        )
        if result.scalars().first():
            raise ChemicalOperationException(
                f"Chemical operation with source {operation_data.source} and target {operation_data.target} already exists"
            )

        try:
            result = await self.db_session.execute(
                insert(ChemicalOperation).values(
                    source_ids=operation_data.source,
                    target_id=target_id,
                    temperature=operation_data.temperature,
                    additional_conditions=operation_data.conditions
                ).returning(ChemicalOperation)
            )
            await self.db_session.commit()
            return result.scalar_one()

        except IntegrityError as e:
            print("IntegrityError raised during INSERT:", e.orig)
            await self.db_session.rollback()
            raise ChemicalOperationException(f"Chemical operation with {operation_data.source} already exists")

    async def delete_chemical_operation(self, target_formula: str, source_formula: str) -> None:
        target_id = await self.get_id_by_formula_normalized(target_formula)
        if not target_id:
            raise HTTPException(
                status_code=404,
                detail=f"Target chemical object with formula {target_formula} not found"
            )

        source_id = await self.get_id_by_formula_normalized(source_formula)
        if not source_id:
            raise HTTPException(
                status_code=404,
                detail=f"Source chemical object with formula {source_formula} not found"
            )
        result = await self.db_session.execute(
            select(ChemicalOperation)
            .where(ChemicalOperation.target_id == target_id)
            .where(source_id == ChemicalOperation.source_ids.any_())
        )
        operation = result.scalars().first()

        if not operation:
            raise HTTPException(
                status_code=404,
                detail=f"No chemical operation found with target {target_formula} and source {source_formula}"
            )

        await self.db_session.execute(
            delete(ChemicalOperation).where(ChemicalOperation.id == operation.id)
        )
        await self.db_session.commit()
