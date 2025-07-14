from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import List, Annotated
from app.chemicals.service.user_service import UserChemicalService
from app.dependency import get_user_chemical_service, get_current_user, get_algorithm
from app.users.user_profile.model import UserProfile
from app.chemicals.algorithms import AlgorithChemicalOperations


router = APIRouter(
    prefix="/chemicals",
    tags=["User Chemical Operations"]
)


@router.get("/transformations", response_model=dict)
async def get_transformations(
        current_user: Annotated[UserProfile, Depends(get_current_user)],
        algorithm: AlgorithChemicalOperations = Depends(get_algorithm),
        main_percent: str = Query(None),
        fe_percent: str = Query(None),
        si_percent: str = Query(None),
        k_percent: str = Query(None),
        ca_percent: str = Query(None),
        mg_percent: str = Query(None),
        na_percent: str = Query(None),
        target_formula: str = Query(...),
        result_mass: int = Query(...)
):
    try:
        percents_data = {
            k: v for k, v in {
                "main_percent": main_percent,
                "fe_percent": fe_percent,
                "si_percent": si_percent,
                "k_percent": k_percent,
                "ca_percent": ca_percent,
                "mg_percent": mg_percent,
                "na_percent": na_percent
            }.items() if v is not None
        }

        chains_dict = await algorithm.get_chains_by_target_formula(target_formula)
        c_min, c_max = algorithm.boundary_determinant(percents_data)

        if not chains_dict:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No transformation chains found for this formula"
            )

        await algorithm.mass_calculator(chains_dict, result_mass, target_formula, c_max, c_min)

        return {
            "success": True,
            "data": chains_dict,
            "message": "Transformations calculated successfully"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/formulas", response_model=List[str])
async def get_all_formulas(
    current_user: Annotated[UserProfile, Depends(get_current_user)],
    chemical_service: UserChemicalService = Depends(get_user_chemical_service)
):
    return await chemical_service.get_all_target_chemical_objects()
