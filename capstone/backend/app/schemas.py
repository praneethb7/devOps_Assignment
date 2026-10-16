from datetime import datetime
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, AwareDatetime

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
Category = Literal["Electronics", "Sports", "Lab", "Events"]

class EquipmentInput(BaseModel):
    name: Text
    category: Category
    quantity: int = Field(ge=1, le=10000)
    location: Text

class EquipmentOutput(EquipmentInput):
    model_config = ConfigDict(from_attributes=True)
    id: int
    available: int

class LoanInput(BaseModel):
    equipment_id: int = Field(gt=0)
    borrower: Text
    due_at: AwareDatetime

class LoanOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    equipment_id: int
    equipment_name: str
    borrower: str
    due_at: datetime
    created_at: datetime
    returned_at: datetime | None
    status: str
