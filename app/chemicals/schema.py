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
    id: int
    formula: str


class TransformationVariantSchema(BaseModel):
    variant: str
    raw_materials: List[RawMaterialSchema]
    reactions: List[ReactionSchema]
