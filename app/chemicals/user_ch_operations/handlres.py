from fastapi import APIRouter, Depends, Query
from typing import List, Annotated
from app.chemicals.service import ChemicalService
from app.chemicals.schema import TransformationVariantSchema
from app.dependency import get_chemical_service, get_current_user
from app.users.user_profile.model import UserProfile

router = APIRouter(
    prefix="/chemicals",
    tags=["Chemicals"]
)


@router.get("/transformations", response_model=List[TransformationVariantSchema])
async def get_transformations(
    current_user: Annotated[UserProfile, Depends(get_current_user)],
    target_formula: str = Query(...),
    chemical_service: ChemicalService = Depends(get_chemical_service),
):
    return await chemical_service.find_transformation(target_formula=target_formula)


@router.get("/formulas", response_model=List[str])
async def get_all_formulas(
    current_user: Annotated[UserProfile, Depends(get_current_user)],
    chemical_service: ChemicalService = Depends(get_chemical_service)
):
    return await chemical_service.get_all_chemical_objects()