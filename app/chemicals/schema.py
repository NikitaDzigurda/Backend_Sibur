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


class RawMaterialSchema(BaseModel):
    id: int | None = None
    formula: str
    source_check: bool
    molar_mass: int


class TransformationVariantSchema(BaseModel):
    variant: str
    raw_materials: List[RawMaterialSchema]
    reactions: List[ReactionSchema]


class ChemicalBoundaryInput(BaseModel):
    main_percent: Optional[str]
    fe_percent: Optional[str]
    si_percent: Optional[str]
    k_percent: Optional[str]
    ca_percent: Optional[str]
    mg_percent: Optional[str]
    na_percent: Optional[str]