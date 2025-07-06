from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from typing import List, Optional, Sequence, Dict
from app.chemicals.models import ChemicalObject, ChemicalOperation

import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


@dataclass
class ChemicalRepository:
    db_session: AsyncSession

    async def get_all_chemical_objects(self):
        result = await self.db_session.execute(select(ChemicalObject.chemical_formula))
        return result.scalars().all()

    async def get_chemical_object(self, id: int) -> Optional[ChemicalObject]:
        result = await self.db_session.execute(
            select(ChemicalObject).where(ChemicalObject.id == id)
        )
        return result.scalar_one_or_none()

    async def get_chemical_objects(self, ids: List[int]) -> Sequence[ChemicalObject]:
        result = await self.db_session.execute(
            select(ChemicalObject).where(ChemicalObject.id.in_(ids)))
        ids = result.scalars().all()
        return list(ids) if isinstance(ids, list) else [ids]

    async def get_operation(self, id: int) -> Optional[ChemicalOperation]:
        result = await self.db_session.execute(
            select(ChemicalOperation).where(ChemicalOperation.id == id))
        return result.scalar_one_or_none()

    async def get_operations_by_target(self, target_id: int) -> Sequence[ChemicalOperation]:
        result = await self.db_session.execute(
            select(ChemicalOperation)
            .where(ChemicalOperation.target_id == target_id)
        )
        ids = result.scalars().all()
        return list(ids) if isinstance(ids, list) else [ids]

    async def find_operations_by_sources(self, source_ids: List[int]) -> Sequence[ChemicalOperation]:
        if not source_ids:
            return []
        return (await self.db_session.execute(
            select(ChemicalOperation)
            .where(ChemicalOperation.source_ids.overlap(source_ids))
        )).scalars().all()

    async def get_ids_by_formulas(self, formulas: List[str]) -> Sequence[int]:
        result = await self.db_session.execute(
            select(ChemicalObject.id)
            .where(ChemicalObject.chemical_formula.in_(formulas))
        )
        ids = result.scalars().all()
        return list(ids) if isinstance(ids, list) else [ids]

    async def get_id_by_formula(self, formula: str) -> int:
        result = await self.db_session.execute(
            select(ChemicalObject.id)
            .where(ChemicalObject.chemical_formula == formula)
        )
        return result.scalar_one()

    async def get_source_ids_by_target(self, target_id: int) -> List[int]:
        result = await self.db_session.execute(
            select(ChemicalOperation.source_ids)
            .where(ChemicalOperation.target_id == target_id)
        )
        source_id_lists = result.scalars().all()
        return list({id for sublist in source_id_lists for id in sublist})

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

    async def find_transformations(
            self,
            source_formulas: List[str],
            target_formula: str
    ) -> List[Dict]:
        """
        Находит все цепочки преобразований из исходных формул в целевую формулу.

        :param source_formulas: Список исходных химических формул
        :param target_formula: Целевая химическая формула
        :return: Список словарей с ключом 'path' содержащим массивы ID операций
        """
        # Получаем ID для исходных формул
        source_ids = await self.get_ids_by_formulas(source_formulas)
        if not source_ids:
            return []

        # Получаем ID для целевой формулы
        target_id = await self.get_id_by_formula(target_formula)
        if not target_id:
            return []

        # Текстуальный SQL-запрос с параметрами
        query = text("""
        WITH RECURSIVE transformation_chains AS (
            -- Стартовая часть
            SELECT 
                r.source_ids,
                r.target_id,
                r.source_ids AS path_materials,
                ARRAY[r.id] AS reaction_chain
            FROM chemicaloperations r
            WHERE r.source_ids && :source_ids

            UNION ALL

            -- Рекурсивная часть
            SELECT 
                r.source_ids,
                r.target_id,
                tc.path_materials || r.source_ids,
                tc.reaction_chain || r.id
            FROM chemicaloperations r
            JOIN transformation_chains tc ON tc.target_id = ANY(r.source_ids)
            WHERE NOT (r.source_ids && tc.path_materials)
        )
        SELECT reaction_chain 
        FROM transformation_chains
        WHERE target_id = :target_id
        """)

        result = await self.db_session.execute(
            query,
            {
                'source_ids': source_ids,
                'target_id': target_id
            }
        )

        return [{'path': row[0]} for row in result]
