from datetime import datetime
from uuid import UUID
from sqlmodel import SQLModel
from typing import Optional
from pydantic import BaseModel

class EquipmentResponse(SQLModel):
    uid: UUID
    dataset_uid: UUID
    equipment_name: str
    equipment_type: str
    flowrate: float
    pressure: float
    temperature: float
    created_at: datetime
    updated_at: datetime

class EquipmentUpdate(SQLModel):
    equipment_name: Optional[str] = None
    equipment_type: Optional[str] = None
    flowrate: Optional[float] = None
    pressure: Optional[float] = None
    temperature: Optional[float] = None
    
class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool

class PaginationEquipmentResponse(BaseModel):
    items: list[EquipmentResponse]
    pagination: PaginationMeta