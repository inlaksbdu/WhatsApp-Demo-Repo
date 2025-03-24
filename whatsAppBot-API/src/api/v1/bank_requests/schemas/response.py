from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from .request import RequestStatus

class BankRequestResponse(BaseModel):
    id: int
    email: str
    customer_name: str
    reference_code: str
    service_type: str
    service_details: Dict[str, Any]
    status: RequestStatus
    created_at: datetime
    processed_at: Optional[datetime] = None
    processed_by: Optional[str] = None
    processing_notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    expiry_date: Optional[datetime] = None
    last_status_update: datetime
    
    class Config:
        from_attributes = True

class PaginatedBankRequestResponse(BaseModel):
    items: List[BankRequestResponse]
    total: int
    page: int
    size: int
    pages: int

class RequestStatusUpdateResponse(BaseModel):
    id: int
    status: RequestStatus
    message: str
