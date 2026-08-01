import uuid
from typing import List,Optional,Literal
from fastapi import APIRouter,Depends,HTTPException,status
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.main import get_session
from src.db.models import User,Equipment
from .schemas import EquipmentResponse,EquipmentUpdate,PaginationEquipmentResponse
from .service import EquipmentService
from fastapi import Query
from src.error import NoEquipmentAvailable,EquipmentNotFound,NoEquipmentForDataset
from src.auth.authorization import (get_current_user,require_dataset_owner,require_equipment_owner,require_dataset_delete_permission)
equipment_service = EquipmentService()
equipment_router =  APIRouter()
@equipment_router.get("/",response_model=PaginationEquipmentResponse,
                      status_code=status.HTTP_200_OK,)
async def get_all_equipment(current_user: User = Depends(get_current_user),session: AsyncSession = Depends(get_session),page:int = Query(default=1,ge=1)
                            ,page_size:int = Query(default=5,ge=1,le=100),search:Optional[str] = None,
                            equipment_name: Optional[str] = None,
                            equipment_type: Optional[str] = None,
                            dataset_uid: Optional[uuid.UUID] = None,min_pressure:Optional[float] = None,
                            max_pressure: Optional[float] = None,min_temperature: Optional[float] = None,
                            max_temperature: Optional[float] = None,min_flowrate:Optional[float] = None,max_flowrate: Optional[float] = None,
                            sort_by: str = Query("created_at"),order:Literal["asc","desc"] = Query("desc")):
    return await equipment_service.get_all_equipments(session,owner_uid=current_user.uid,page=page,page_size=page_size,search=search,
                                                      equipment_name=equipment_name,equipment_type=equipment_type,dataset_uid=dataset_uid,
                                                      min_pressure=min_pressure,max_pressure=max_pressure,min_temperature=min_temperature,
                                                      max_temperature=max_temperature,min_flowrate=min_flowrate,max_flowrate=max_flowrate,
                                                      sort_by=sort_by,order=order)
@equipment_router.get("/{equipment_uid}",response_model=EquipmentResponse,
                      status_code=status.HTTP_200_OK)
async def get_equipment(equipment_uid:uuid.UUID,current_user: User = Depends(get_current_user),
                        session: AsyncSession = Depends(get_session),):
    equipment = await equipment_service.get_equipment_by_uid(current_user.uid,equipment_uid,session)
    if equipment is None:
        raise EquipmentNotFound()
    
    return equipment

@equipment_router.get("/dataset/{dataset_uid}",
                      response_model = List[EquipmentResponse],
                      status_code=status.HTTP_200_OK)
async def get_equipment_by_dataset(dataset=Depends(require_dataset_owner),
    session: AsyncSession = Depends(get_session)):
    equipments =  await equipment_service.get_equipment_by_dataset(dataset.uid,session)
    if equipments:
        return equipments
    else:
        raise NoEquipmentForDataset()

@equipment_router.patch("/{equipment_uid}",response_model=EquipmentResponse,
                        status_code= status.HTTP_200_OK)
async def update_equipment(update_data: EquipmentUpdate,
                           equipment: Equipment = Depends(require_equipment_owner),
                           session: AsyncSession = Depends(get_session)):
    equipment = await equipment_service.update_equipment(
        equipment.uid,update_data,session
    )
    if equipment is None:
        raise EquipmentNotFound()
    return equipment

@equipment_router.delete("/{equipment_uid}",
                         status_code=status.HTTP_200_OK)
async def delete_equipment(equipment: Equipment = Depends(require_equipment_owner),
                           session: AsyncSession = Depends(get_session)):
    deleted = await equipment_service.delete_equipment(
        equipment.uid,session)
    if deleted is None:
        raise EquipmentNotFound()
    return {
        "message": "Equipment deleted successfully."
    }



