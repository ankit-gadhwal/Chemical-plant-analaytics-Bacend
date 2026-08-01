from sqlmodel import SQLModel

class AnalyticsSummary(SQLModel):
    total_equipment: int
    average_flowrate: float
    average_pressure: float
    average_temperature: float
    