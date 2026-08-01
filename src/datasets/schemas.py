import uuid
from datetime import datetime
from sqlmodel import SQLModel
from typing import Dict,List,Optional
from pydantic import BaseModel
from src.db.models import Datasetstatus

class DatasetUpdate(SQLModel):
    original_filename: str | None = None

class DatasetResponse(SQLModel):
    uid: uuid.UUID

    original_filename: str

    equipment_count: Optional[int] = None

    average_flowrate: Optional[float] = None
    average_pressure: Optional[float] = None
    average_temperature: Optional[float] = None

    equipment_summary: Optional[dict] = None
    status: Datasetstatus
    created_at: datetime

class ParameterStatistics(BaseModel):
    min: Optional[float] = None
    max: Optional[float] = None
    average: Optional[float] = None

class DatasetStatistics(BaseModel):
    flowrate: ParameterStatistics
    pressure: ParameterStatistics
    temperature: ParameterStatistics

class DatasetDetailResponse(SQLModel):

    uid: uuid.UUID
    original_filename: str
    stored_filename: str
    file_path: str
    equipment_count: Optional[int] = None

    statistics: DatasetStatistics

    equipment_summary: Optional[Dict[str, int]] = None

    inactive_equipment: Optional[List[Dict]] = None
    missing_data: Optional[List[Dict]] = None
    created_at: datetime
    updated_at: datetime

class DatasetUploadResponse(SQLModel):
    uid:uuid.UUID
    original_filename: str
    message: str

class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool

class PaginationEquipmentResponse(BaseModel):
    items: list[DatasetResponse]
    pagination: PaginationMeta

class UploadedFileInfo(BaseModel):
    original_filename: str
    stored_filename: str
    file_path: str

class DatasetSummary(BaseModel):
    equipment_count: int
    average_flowrate: float
    average_pressure: float
    average_temperature: float
    min_flowrate: float
    max_flowrate: float
    min_pressure: float
    max_pressure: float
    min_temperature: float
    max_temperature: float
    equipment_summary: dict[str, int]