import uuid
from sqlmodel import select,desc
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.exceptions import HTTPException
from src.db.models import Equipment,Dataset
from .schemas import EquipmentUpdate
from datetime import datetime
from sqlalchemy import func,asc,desc,or_
import math
from typing import Optional,Literal
from src.logger import logger

class EquipmentService:
    async def page_info(self,page,page_size,count_statements,session:AsyncSession):
        
        count_result = await session.exec(count_statements)
        total_items = count_result.one()
        total_pages = math.ceil(total_items/page_size)
        has_next = page < total_pages
        has_previous = page > 1
        offset = (page-1) * page_size
        return total_items,total_pages,has_next,has_previous,offset
    
    async def get_all_equipments(self,session:AsyncSession,owner_uid:uuid.UUID,page: int,page_size: int,search: Optional[str] = None,
                                 equipment_name: str | None = None,equipment_type: str | None = None,
                                 dataset_uid: uuid.UUID | None = None,min_pressure: float | None = None,
                                 max_pressure: float | None = None,min_temperature: float | None = None,
                                 max_temperature: float | None = None,min_flowrate: float | None = None,
                                 max_flowrate: float | None = None,sort_by:str="created_at",order:Literal["asc","desc"] = "desc"):
        
        logger.info(f"Fetching equipments (page={page}, page_size={page_size})")
        statement = (select(Equipment).join(Dataset).where(Dataset.owner_uid == owner_uid)
)
        if search:
            statement = statement.where(or_(
                Equipment.equipment_name.ilike(f"%{search}%"),
                Equipment.equipment_type.ilike(f"%{search}%")
            ))
        if equipment_name:
            statement = statement.where(Equipment.equipment_name.ilike(f"%{equipment_name}%"))
        
        if equipment_type:
            statement = statement.where(Equipment.equipment_type == equipment_type)
        
        if dataset_uid:
            statement = statement.where(Equipment.dataset_uid == dataset_uid)
        
        if min_pressure is not None:
            statement = statement.where(Equipment.pressure >= min_pressure)
        
        if max_pressure is not None:
            statement = statement.where(Equipment.pressure <= max_pressure) 

        if min_temperature is not None:
            statement = statement.where(Equipment.temperature >= min_temperature)  

        if max_temperature is not None:
            statement = statement.where(Equipment.temperature <= max_temperature)

        if min_flowrate is not None:
            statement = statement.where(Equipment.flowrate >= min_flowrate) 
        
        if max_flowrate is not None:
            statement = statement.where(Equipment.flowrate <= max_flowrate)

        count_statements = select(func.count()).select_from(statement.subquery())
        (total_items,total_pages,has_next,has_previous,offset) = await self.page_info(page,page_size,count_statements,session)
        sort_columns = {
            "equipment_name":Equipment.equipment_name,
            "equipment_type":Equipment.equipment_type,
            "pressure":Equipment.pressure,
            "temperature":Equipment.temperature,
            "flowrate":Equipment.flowrate,
            "created_at":Equipment.created_at
        }
        column = sort_columns.get(sort_by,Equipment.created_at)
        if order == "asc":
            statement = statement.order_by(asc(column))
        else:
            statement = statement.order_by(desc(column))
        statement = statement.offset(offset).limit(page_size)

        result = await session.exec(statement)
        equipments = result.all()
        logger.info(f"Returned {len(equipments)} equipments")
        return {
            "items":equipments,
            "pagination":{
                "page":page,
                "page_size":page_size,
                "total_items": total_items,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_previous": has_previous,
            }
        }
    
    async def get_equipment_by_uid(self,owner_uid:uuid.UUID,equipment_uid:uuid.UUID,session: AsyncSession):
        logger.info(f"Fetching equipment: {equipment_uid}")
        statement = (select(Equipment).join(Dataset).where(Equipment.uid == equipment_uid,Dataset.owner_uid == owner_uid))

        result = await session.exec(statement)

        equipment = result.first()
        if equipment is not None:
            logger.info("Equipment found")
            return equipment  
        else:
            logger.warning(f"Equipment not found: {equipment_uid}")
            return None 
    
    async def get_equipment_by_dataset(self,equipment_dataset_uid:uuid.UUID,session: AsyncSession):
        logger.info(f"Fetching Equipment_dataset: {equipment_dataset_uid}")
        statement = select(Equipment).where(Equipment.dataset_uid == equipment_dataset_uid)

        result = await session.exec(statement)

        equipments = result.all()
        
        logger.info("equimpent belongs dataset found")
        return equipments
    
    async def update_equipment(
        self, equipment_uid: uuid.UUID, update_data: EquipmentUpdate, session: AsyncSession
    ) ->Equipment:
        logger.info(f"Updating equipment: {equipment_uid}")
        statement = select(Equipment).where(Equipment.uid == equipment_uid)
        result = await session.exec(statement)
        equipment_to_update = result.first()

        if equipment_to_update is not None:
            update_data_dict = update_data.model_dump(exclude_unset=True)
            for key, value in update_data_dict.items():
                setattr(equipment_to_update, key, value)
            equipment_to_update.updated_at = datetime.now()
            await session.commit()
            await session.refresh(equipment_to_update)
            logger.info("Equipment updated successfully")
            return equipment_to_update
        else:
            logger.warning(f"Equipment not found: {equipment_uid}")
            return None

    async def delete_equipment(self,equipment_uid:uuid.UUID, session:AsyncSession)->None:
        statement = select(Equipment).where(Equipment.uid == equipment_uid)
        result = await session.exec(statement)
        equipment_to_delete = result.first()
        logger.info(f"Deleting equipment: {equipment_uid}")
        if equipment_to_delete is not None:
            await session.delete(equipment_to_delete)

            await session.commit()
            
            logger.info("Equipment deleted successfully")
            return {
                "message": "Equipment deleted successfully."
            }

        else:
            logger.warning(f"Equipment not found: {equipment_uid}")
            return None

    