from fastapi import APIRouter, Depends, status

from app.dependency import *
from app.chemicals.repository import *


router = APIRouter(prefix="/admin", tags=["Admin Chemical Operations"])


@router.get("/table/{table_name}", status_code=status.HTTP_200_OK)
async def get_full_table(
        model_name: str,
        service: Annotated[AdminChemicalService, Depends(get_admin_chemical_service)],
        admin_user: Annotated[UserProfile, Depends(get_current_admin_user)]):
    model_mapping = {
        "userprofile": UserProfile,
        "chemicalobjects": ChemicalObject,
        "chemicaloperations": ChemicalOperation,
        "percentchemicalelements": PercentChemicalElements
    }

    if model_name not in model_mapping:
        raise HTTPException(
            status_code=404,
            detail=f"Model {model_name} not found"
        )

    return await service.get_table_data(model_mapping[model_name], admin_user.login)


@router.get("/tables/", status_code=status.HTTP_200_OK)
async def get_all_tables(
        admin_user: Annotated[UserProfile, Depends(get_current_admin_user)],
        service: Annotated[AdminChemicalService, Depends(get_admin_chemical_service)]):
    return await service.get_all_tables(admin_login=admin_user.login)


@router.post("/materials", status_code=status.HTTP_201_CREATED)
async def add_new_material(
        material_data: RawMaterialSchema,
        service: Annotated[AdminChemicalService, Depends(get_admin_chemical_service)],
        admin_user: Annotated[UserProfile, Depends(get_current_admin_user)],
):
    try:
        new_material = await service.create_chemical_object(
            admin_login=admin_user.login,
            new_chemical_object=material_data
        )
        return {
            "message": "New material added successfully",
            "chemical_formula": new_material.chemical_formula,
            "source_check": new_material.source_check,
            "molar_mass": new_material.molar_mass,
            "new_material_id": new_material.id
        }

    except ChemicalObjectExistsException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e))


@router.delete("/chemical/{object_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chemical(
    chemical_object: str,
    service: Annotated[AdminChemicalService, Depends(get_admin_chemical_service)],
    admin_user: Annotated[UserProfile, Depends(get_current_admin_user)],
):
    await service.delete_chemical_object(
        chemical_object=chemical_object,
        admin_login=admin_user.login
    )


@router.post("/chemical-composition", status_code=status.HTTP_201_CREATED)
async def add_chemical_with_composition(
    composition_data: ChemicalCompositionSchema,
    service: Annotated[AdminChemicalService, Depends(get_admin_chemical_service)],
    admin_user: Annotated[UserProfile, Depends(get_current_admin_user)],
):
    try:
        result = await service.add_chemical_with_composition(
            admin_login=admin_user.login,
            composition_data=composition_data
        )
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.delete("/chemical-composition", status_code=status.HTTP_200_OK)
async def delete_chemical_composition(
    delete_data: MetalCompositionDelete,
    service: Annotated[AdminChemicalService, Depends(get_admin_chemical_service)],
    admin_user: Annotated[UserProfile, Depends(get_current_admin_user)],
):
    try:
        result = await service.delete_chemical_composition(
            admin_login=admin_user.login,
            delete_data=delete_data
        )
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/chemical-operation", status_code=status.HTTP_201_CREATED)
async def create_chemical_operation(
    operation_data: OperationsSchema,
    service: Annotated[AdminChemicalService, Depends(get_admin_chemical_service)],
    admin_user: Annotated[UserProfile, Depends(get_current_admin_user)],
):
    try:
        result = await service.create_chemical_operation(
            admin_login=admin_user.login,
            operation_data=operation_data
        )
        return result

    except HTTPException as e:
        raise e

    except IntegrityError as e:
        await service.chemical_repository.db_session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database integrity error: {str(e.orig)}"
        )

    except Exception as e:
        await service.chemical_repository.db_session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.delete("/chemical-operation", status_code=status.HTTP_200_OK)
async def delete_chemical_operation(
        delete_data: OperationDeleteSchema,
        service: Annotated[AdminChemicalService, Depends(get_admin_chemical_service)],
        admin_user: Annotated[UserProfile, Depends(get_current_admin_user)],
):
    try:
        result = await service.delete_chemical_operation(
            admin_login=admin_user.login,
            target_formula=delete_data.target_formula,
            source_formula=delete_data.source_formula
        )
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
