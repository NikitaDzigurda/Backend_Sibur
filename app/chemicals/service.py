from dataclasses import dataclass

from app.chemicals import ChemicalRepository
from app.chemicals.schema import *


@dataclass
class ChemicalService:
    chemical_repository: ChemicalRepository

    async def get_all_chemical_objects(
            self
    ) -> List[str]:
        return await self.chemical_repository.get_all_chemical_objects()

    async def find_transformation(
            self,
            target_formula: str,
    ) -> List[TransformationVariantSchema]:
        id_target_formula = await self.chemical_repository.get_id_by_formula(target_formula)
        chemical_sources = await self.chemical_repository.get_source_formulas_by_target_id(id_target_formula)

        transformations = await self.chemical_repository.find_transformations(
            target_formula=target_formula,
            source_formulas=chemical_sources
        )

        result = []
        for idx, path in enumerate(transformations, 1):
            operation_ids = path["path"]

            operations_list = [
                await self.chemical_repository.get_operation(op_id) for op_id in operation_ids
            ]

            all_source_ids = set()
            all_target_ids = set()
            for op in operations_list:
                all_source_ids.update(op.source_ids)
                all_target_ids.add(op.target_id)

            all_object_ids = list(all_source_ids | all_target_ids)
            objects = await self.chemical_repository.get_chemical_objects(all_object_ids)
            obj_by_id = {obj.id: obj for obj in objects}

            raw_materials = [
                RawMaterialSchema(
                    id=obj.id,
                    formula=obj.chemical_formula
                )
                for obj in objects
                if obj.id in all_source_ids
            ]

            reactions = []
            for i, op in enumerate(operations_list, 1):
                sources = [obj_by_id[sid].chemical_formula for sid in op.source_ids]
                product = obj_by_id[op.target_id].chemical_formula

                reactions.append(ReactionSchema(
                    index=i,
                    conditions=ReactionConditions(
                        temperature=op.temperature,
                        extra=op.additional_conditions
                    ),
                    sources=sources,
                    product=product
                ))

            result.append(TransformationVariantSchema(
                variant=f"Вариант {idx}",
                raw_materials=raw_materials,
                reactions=reactions
            ))

        return result


