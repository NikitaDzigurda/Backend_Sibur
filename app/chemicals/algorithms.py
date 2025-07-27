from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import pulp
from math import gcd

import logging
from sqlalchemy import text
from catboost import CatBoostRegressor
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class AlgorithChemicalOperations:
    db_session: AsyncSession

    @staticmethod
    def _al_coeff(s):
        coeff_index = s.find("Al") + 3
        if coeff_index < len(s) and s[coeff_index].isdigit():
            return int(s[coeff_index])
        else:
            return 1

    @staticmethod
    def boundary_determinant(percentage_dict: dict[str, str]) -> tuple[dict[str, float], dict[str, float]]:
        C_min = {}
        C_max = {}

        for key, value in percentage_dict.items():
            value = value.strip()

            if value.startswith(">"):
                C_min[key] = float(value[1:]) / 100
                C_max[key] = 1.0

            elif value.startswith("<"):
                C_min[key] = 0.0
                C_max[key] = float(value[1:]) / 100

            elif "-" in value:
                try:
                    min_str, max_str = map(str.strip, value.split("-", 1))
                    C_min[key] = float(min_str) / 100
                    C_max[key] = float(max_str) / 100
                except ValueError:
                    raise ValueError(f"Invalid range format for {key}: {value}")

            else:
                raise ValueError(f"Unsupported value format for {key}: {value}")

        return C_min, C_max

    async def get_chains_by_target_formula(self, target_formula: str):
        logger.info(f"Executing get_chains_by_target_formula with target_formula: {target_formula}")

        initial_query = text("""
            WITH RECURSIVE transformation_chains AS (
                SELECT 
                    r.source_ids,
                    r.target_id,
                    r.source_ids AS path_materials,
                    ARRAY[r.id] AS reaction_chain
                FROM chemicaloperations r
                WHERE (r.source_ids) && ARRAY(
                    SELECT id
                    FROM chemicalobjects
                    WHERE source_check = 'true'
                )
                UNION ALL
                SELECT 
                    r.source_ids,
                    r.target_id,
                    tc.path_materials || r.source_ids,
                    tc.reaction_chain || r.id
                FROM chemicaloperations r
                JOIN transformation_chains tc ON 
                    tc.target_id = ANY(r.source_ids)
                WHERE 
                    NOT (r.source_ids && tc.path_materials)
            )
            SELECT * 
            FROM transformation_chains
            WHERE 
                (SELECT id FROM chemicalobjects WHERE chemical_formula = :target_formula) = target_id;
        """)
        try:
            result1 = await self.db_session.execute(initial_query, {"target_formula": target_formula})
            rows = result1.fetchall()
            logger.info(f"Query result: {rows}")

            chains = [row[3] for row in rows]
            chains_dict = {}
            variant_cnt = 0

            for chain in chains:
                reactions_table = []
                for reaction_id in chain:
                    chain_query = text("""
                        SELECT *
                        FROM chemicaloperations
                        WHERE id = :reaction_id
                    """)
                    result2 = await self.db_session.execute(chain_query, {"reaction_id": reaction_id})
                    rows = result2.fetchall()
                    reactions_table.append(rows)
                    logger.info(f"Reaction ID {reaction_id} result: {rows}")

                first_reaction_row = reactions_table[0][0]
                for first_material_id in first_reaction_row[1]:
                    steps_dict = {}
                    materials_dict = {}

                    first_material_in_warehouse_query = text("""
                        SELECT *
                        FROM percentchemicalelements
                        WHERE type_id = :first_material_id
                    """)
                    result3 = await self.db_session.execute(first_material_in_warehouse_query,
                                                            {"first_material_id": first_material_id})
                    fm_types_table = result3.fetchall()
                    logger.info(f"PercentChemicalElements for material ID {first_material_id}: {fm_types_table}")

                    fm_formula_query = text("""
                        SELECT chemical_formula
                        FROM chemicalobjects
                        WHERE id = :first_material_id
                    """)
                    result4 = await self.db_session.execute(fm_formula_query, {"first_material_id": first_material_id})
                    fm_formula = result4.fetchall()[0][0]
                    logger.info(f"Formula for material ID {first_material_id}: {fm_formula}")

                    molar_mass_query = text("""
                        SELECT molar_mass
                        FROM chemicalobjects
                        WHERE id = :first_material_id
                    """)
                    result5 = await self.db_session.execute(molar_mass_query, {"first_material_id": first_material_id})
                    molar_mass = result5.fetchall()[0][0]
                    logger.info(f"Molar mass for material ID {first_material_id}: {molar_mass}")

                    for sourse_type_row in fm_types_table:
                        unical_id = str(sourse_type_row[0])
                        main_percent = str(sourse_type_row[2])
                        fe_percent = str(sourse_type_row[3])
                        si_percent = str(sourse_type_row[4])
                        k_percent = str(sourse_type_row[5])
                        ca_percent = str(sourse_type_row[6])
                        mg_percent = str(sourse_type_row[7])
                        na_percent = str(sourse_type_row[8])
                        materials_dict[unical_id] = {
                            "main_percent": main_percent,
                            "fe_percent": fe_percent,
                            "si_percent": si_percent,
                            "k_percent": k_percent,
                            "ca_percent": ca_percent,
                            "mg_percent": mg_percent,
                            "na_percent": na_percent,
                            "mass": 0
                        }
                    materials_dict["molar_mass"] = molar_mass
                    materials_dict["formula"] = fm_formula

                    reaction_conditions = '; '.join(list(map(str, first_reaction_row[3:])))

                    target = first_reaction_row[2]
                    target_formula_query = text("""
                        SELECT chemical_formula
                        FROM chemicalobjects
                        WHERE id = :target_id
                    """)
                    result6 = await self.db_session.execute(target_formula_query, {"target_id": target})
                    target_formula_result = result6.fetchall()[0][0]
                    logger.info(f"Target formula for ID {target}: {target_formula_result}")

                    steps_dict["Шаг 1"] = {
                        "Условия проведения реакции": reaction_conditions,
                        "Входные элементы": materials_dict,
                        "Продукт реакции": target_formula_result
                    }

                    for i in range(1, len(reactions_table)):
                        reaction_row = reactions_table[i][0]
                        reaction_conditions = '; '.join(list(map(str, reaction_row[3:])))

                        target_id = reaction_row[2]
                        target_formula_query = text("""
                            SELECT chemical_formula
                            FROM chemicalobjects
                            WHERE id = :target_id
                        """)
                        result7 = await self.db_session.execute(target_formula_query, {"target_id": target_id})
                        target_formula = result7.fetchall()[0][0]

                        source_id = reaction_row[1][0]
                        source_formula_query = text("""
                            SELECT chemical_formula
                            FROM chemicalobjects
                            WHERE id = :source_id
                        """)
                        result8 = await self.db_session.execute(source_formula_query, {"source_id": source_id})
                        source_formula = result8.fetchall()[0][0]
                        steps_dict[f"Шаг {i + 1}"] = {
                            "Условия проведения реакции": reaction_conditions,
                            "Входные элементы": source_formula,
                            "Продукт реакции": target_formula
                        }

                    variant_cnt += 1
                    chains_dict[f"Вариант {variant_cnt}"] = steps_dict

            logger.info(f"Returning chains_dict: {chains_dict}")
            return chains_dict
        except Exception as e:
            logger.error(f"Error in get_chains_by_target_formula: {str(e)}", exc_info=True)
            raise

    async def mass_calculator(self, chains_dict, M_target, target_formula, C_max, C_min):
        for variant in chains_dict.keys():

            molar_mass_source = float(chains_dict[variant]["Шаг 1"]["Входные элементы"]["molar_mass"])
            source_formula = chains_dict[variant]["Шаг 1"]["Входные элементы"]["formula"]
            molar_mass_target_query = text(f"""
                        SELECT molar_mass
                        FROM chemicalobjects
                        WHERE chemical_formula = '{target_formula}'
            """)
            result1 = await self.db_session.execute(molar_mass_target_query)
            molar_mass_target = float(result1.fetchall()[0][0])

            Al_coeff_source = self._al_coeff(source_formula)
            Al_coeff_target = self._al_coeff(target_formula)
            nok = Al_coeff_source * Al_coeff_target // gcd(Al_coeff_source, Al_coeff_target)

            ratio = ((nok // Al_coeff_target * molar_mass_target) /
                     (nok // Al_coeff_source * molar_mass_source))

            components = [component for component in chains_dict[variant]["Шаг 1"]["Входные элементы"].keys()][:-2]

            c = {}
            for component in components:
                for percentage in [p for p in chains_dict[variant]["Шаг 1"]["Входные элементы"][component].keys()][:-1]:
                    c[(component, percentage)] = float(
                        chains_dict[variant]["Шаг 1"]["Входные элементы"][component][percentage]) / 100

            x = pulp.LpVariable.dicts('mass', components, lowBound=0)

            model = pulp.LpProblem("Mixing", pulp.LpMinimize)

            model += pulp.lpSum(ratio * x[i] for i in components) == M_target, "MassBalance"

            for j in C_max:
                if j == 'main_percent':
                    expr = pulp.lpSum(c[(i, j)] * ratio * x[i] for i in components) / M_target
                    model += expr <= C_max[j], f"{j}_max"
                    model += expr >= C_min[j], f"{j}_min"
                else:
                    expr = pulp.lpSum(c[(i, j)] * x[i] for i in components) / M_target
                    model += expr <= C_max[j], f"{j}_max"
                    model += expr >= C_min[j], f"{j}_min"

            model += pulp.lpSum(x[i] for i in components)

            model.solve()

            status = pulp.LpStatus[model.status]

            if status != 'Optimal':
                chains_dict[variant] = "Не удаётся подобрать массы"
            else:
                answer_dict = {}
                for i in components:
                    val = x[i].value()
                    answer_dict[i] = val
                    if val and val > 1e-6:
                        chains_dict[variant]['Шаг 1']['Входные элементы'][i]['mass'] = val
                    else:
                        chains_dict[variant]['Шаг 1']['Входные элементы'][i]['mass'] = 0

    @staticmethod
    async def sort_chains_by_complexity(chains_dict: dict) -> dict:
        try:
            loaded_model = CatBoostRegressor()
            loaded_model.load_model('model.cbm')
        except Exception as e:
            logger.error(f"Failed to load CatBoost model: {str(e)}", exc_info=True)
            raise ValueError("Unable to load complexity prediction model")

        pop_list = [variant for variant in chains_dict if chains_dict[variant] == "Не удаётся подобрать массы"]
        for variant in pop_list:
            chains_dict.pop(variant)

        variants_complexity = {}
        for variant in chains_dict:
            chain_complexity = 0
            for step in chains_dict[variant]:
                conditions = chains_dict[variant][step].get("Условия проведения реакции", "")
                if not conditions:
                    continue

                temperature, *additional_conditions = conditions.split('; ')
                additional_conditions = [cond.strip() for cond in additional_conditions]
                additional_conditions = [cond for cond in additional_conditions if cond]

                conditions_dict = {"temperature": temperature if temperature else "0"}
                for condition in additional_conditions:
                    if "MPa" in condition:
                        conditions_dict["MPa"] = condition.split()[0]
                    elif "microimpurit" in condition:
                        conditions_dict["microimpurities"] = 1
                    else:
                        conditions_dict[condition] = 1

                data = {
                    "temperature": [float(conditions_dict.get("temperature", 0))],
                    "MPa": [float(conditions_dict.get("MPa", 0))],
                    "hydrothermal process": [int(conditions_dict.get("hydrothermal process", 0))],
                    "vacuum": [int(conditions_dict.get("vacuum", 0))],
                    "microimpurities": [int(conditions_dict.get("microimpurities", 0))],
                    "equilibrium crystallization": [int(conditions_dict.get("equilibrium crystallization", 0))],
                    "nonequilibrium crystallization": [int(conditions_dict.get("nonequilibrium crystallization", 0))]
                }

                conditions_df = pd.DataFrame(data)
                reaction_complexity = loaded_model.predict(conditions_df)[0]
                chain_complexity += reaction_complexity

            variants_complexity[variant] = chain_complexity

        sorted_variants_complexity = dict(sorted(variants_complexity.items(), key=lambda item: item[1]))

        final_dict = {}
        i = 0
        for variant in sorted_variants_complexity:
            i += 1
            final_dict[f"Вариант {i}"] = chains_dict[variant]

        return final_dict




