from pydantic import BaseModel
from typing import List, Optional


class ReactionConditions(BaseModel):
    temperature: Optional[float]
    extra: Optional[str]


class ReactionSchema(BaseModel):
    index: int
    conditions: ReactionConditions
    sources: List[str]
    product: str


class OperationsSchema(BaseModel):
    source: List[int]
    target: str
    temperature: int
    conditions: str


class RawMaterialSchema(BaseModel):
    id: int | None = None
    formula: str
    source_check: str
    molar_mass: int


class TransformationVariantSchema(BaseModel):
    variant: str
    raw_materials: List[RawMaterialSchema]
    reactions: List[ReactionSchema]


class MetalComposition(BaseModel):
    main_percent: float
    Fe_percent: float
    Si_percent: float
    K_percent: float
    Ca_percent: float
    Mg_percent: float
    Na_percent: float


class ChemicalCompositionSchema(BaseModel):
    formula: str
    metal_composition: MetalComposition


class MetalCompositionDelete(BaseModel):
    chemical_formula: str
    main_percent: float
    Fe_percent: float
    Si_percent: float
    K_percent: float
    Ca_percent: float
    Mg_percent: float
    Na_percent: float


class OperationDeleteSchema(BaseModel):
    target_formula: str
    source_formula: str
