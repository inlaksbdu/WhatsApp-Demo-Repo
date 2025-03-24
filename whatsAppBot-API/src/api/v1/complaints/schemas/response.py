from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from .request import ComplainStatus

class ComplaintResponse(BaseModel):
    id: int
    name: str
    email: str
    phone_number: str
    complaint_type: str
    description: str
    status: ComplainStatus
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolution_notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    hold_reason: Optional[str] = None
    
    class Config:
        from_attributes = True

class PaginatedComplaintResponse(BaseModel):
    items: List[ComplaintResponse]
    total: int
    page: int
    size: int
    pages: int

class ComplaintStatusUpdateResponse(BaseModel):
    id: int
    status: ComplainStatus
    message: str
