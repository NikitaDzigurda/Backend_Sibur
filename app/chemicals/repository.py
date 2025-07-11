from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, inspect, insert, update, func, delete
from typing import List, Optional, Sequence, Dict, Any
from app.chemicals.models import ChemicalObject, ChemicalOperation, PercentChemicalElements
from app.infrastructure import Base
from app.chemicals.schema import *
from sqlalchemy.exc import IntegrityError

import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


class ChemicalObjectExistsException(Exception):
    pass

# async def get_source_ids_by_target(self, target_id: int) -> List[int]:
#     result = await self.db_session.execute(
#         select(ChemicalOperation.source_ids)
#         .where(ChemicalOperation.target_id == target_id)
#     )
#     source_id_lists = result.scalars().all()
#     return list({id for sublist in source_id_lists for id in sublist})

# async def find_operations_by_sources(self, source_ids: List[int]) -> Sequence[ChemicalOperation]:
#     if not source_ids:
#         return []
#     return (await self.db_session.execute(
#         select(ChemicalOperation)
#         .where(ChemicalOperation.source_ids.overlap(source_ids))
#     )).scalars().all()

# async def get_chemical_object(self, id: int) -> Optional[ChemicalObject]:
#     result = await self.db_session.execute(
#         select(ChemicalObject).where(ChemicalObject.id == id)
#     )
#     return result.scalar_one_or_none()

# async def get_operations_by_target(self, target_id: int) -> Sequence[ChemicalOperation]:
#     result = await self.db_session.execute(
#         select(ChemicalOperation)
#         .where(ChemicalOperation.target_id == target_id)
#     )
#     ids = result.scalars().all()
#     return list(ids) if isinstance(ids, list) else [ids]


@dataclass
class ChemicalRepository:
    db_session: AsyncSession

    async def get_all_target_chemical_objects(self):
        result = await self.db_session.execute(
            select(ChemicalObject.chemical_formula).where(ChemicalObject.source_check.is_(False)))
        return result.scalars().all()

    async def get_chemical_objects(self, ids: List[int]) -> Sequence[ChemicalObject]:
        result = await self.db_session.execute(
            select(ChemicalObject).where(ChemicalObject.id.in_(ids)))
        ids = result.scalars().all()
        return list(ids) if isinstance(ids, list) else [ids]

    async def get_operation(self, id: int) -> Optional[ChemicalOperation]:
        result = await self.db_session.execute(
            select(ChemicalOperation).where(ChemicalOperation.id == id))
        return result.scalar_one_or_none()

    async def get_ids_by_formulas(self, formulas: List[str]) -> Sequence[int]:
        result = await self.db_session.execute(
            select(ChemicalObject.id)
            .where(ChemicalObject.chemical_formula.in_(formulas))
        )
        ids = result.scalars().all()
        return list(ids) if isinstance(ids, list) else [ids]

    async def get_id_by_formula(self, formula: str) -> int:
        print(f"Checking formula in DB: {formula}")
        result = await self.db_session.execute(
            select(ChemicalObject.id)
            .where(ChemicalObject.chemical_formula == formula)
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

    async def get_metal_compositions(self, type_id: int):
        result = await self.db_session.execute(
            select(
                PercentChemicalElements.Fe_percent,
                PercentChemicalElements.Si_percent,
                PercentChemicalElements.K_percent,
                PercentChemicalElements.Ca_percent,
                PercentChemicalElements.Mg_percent,
                PercentChemicalElements.Na_percent
            )
            .where(PercentChemicalElements.type_id == type_id)
        )
        rows = result.all()
        return [
            {
                "Fe": row.Fe_percent,
                "Si": row.Si_percent,
                "K": row.K_percent,
                "Ca": row.Ca_percent,
                "Mg": row.Mg_percent,
                "Na": row.Na_percent
            }
            for row in rows
        ]

    async def get_metal_composition(self, type_id: int, main: float):
        result = await self.db_session.execute(
            select(
                PercentChemicalElements.Fe_percent,
                PercentChemicalElements.Si_percent,
                PercentChemicalElements.K_percent,
                PercentChemicalElements.Ca_percent,
                PercentChemicalElements.Mg_percent,
                PercentChemicalElements.Na_percent
            )
            .where(
                PercentChemicalElements.type_id == type_id,
                PercentChemicalElements.main_percent == main
            )
        )
        rows = result.all()
        return [
            {
                "Fe": row[0],
                "Si": row[1],
                "K": row[2],
                "Ca": row[3],
                "Mg": row[4],
                "Na": row[5]
            }
            for row in rows
        ]

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



    # async def find_transformations(
    #         self,
    #         source_formulas: List[str],
    #         target_formula: str
    # ) -> List[Dict]:
    #     # Получаем ID для исходных формул
    #     source_ids = await self.get_ids_by_formulas(source_formulas)
    #     if not source_ids:
    #         return []
    #
    #     # Получаем ID для целевой формулы
    #     target_id = await self.get_id_by_formula(target_formula)
    #     if not target_id:
    #         return []
    #
    #     # Текстуальный SQL-запрос с параметрами
    #     query = text("""
    #     WITH RECURSIVE transformation_chains AS (
    #         -- Стартовая часть
    #         SELECT
    #             r.source_ids,
    #             r.target_id,
    #             r.source_ids AS path_materials,
    #             ARRAY[r.id] AS reaction_chain
    #         FROM chemicaloperations r
    #         WHERE r.source_ids && :source_ids
    #
    #         UNION ALL
    #
    #         -- Рекурсивная часть
    #         SELECT
    #             r.source_ids,
    #             r.target_id,
    #             tc.path_materials || r.source_ids,
    #             tc.reaction_chain || r.id
    #         FROM chemicaloperations r
    #         JOIN transformation_chains tc ON tc.target_id = ANY(r.source_ids)
    #         WHERE NOT (r.source_ids && tc.path_materials)
    #     )
    #     SELECT reaction_chain
    #     FROM transformation_chains
    #     WHERE target_id = :target_id
    #     """)
    #
    #     result = await self.db_session.execute(
    #         query,
    #         {
    #             'source_ids': source_ids,
    #             'target_id': target_id
    #         }
    #     )
    #
    #     return [{'path': row[0]} for row in result]