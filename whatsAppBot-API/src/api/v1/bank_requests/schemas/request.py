from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from enum import Enum
from datetime import datetime

class RequestStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    ON_HOLD = "on_hold"
    REJECTED = "rejected"

class BankRequestFilter(BaseModel):
    email: Optional[str] = None
    customer_name: Optional[str] = None
    reference_code: Optional[str] = None
    service_type: Optional[str] = None
    status: Optional[RequestStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class UpdateRequestStatusRequest(BaseModel):
    status: RequestStatus = Field(..., description="New status for the bank request")

class RejectRequestRequest(BaseModel):
    rejection_reason: str = Field(..., min_length=5, max_length=500, description="Reason for rejecting the request")

class ResolveRequestRequest(BaseModel):
    processing_notes: str = Field(..., min_length=5, max_length=1000, description="Notes about how the request was processed")
    processed_by: str = Field(..., min_length=2, max_length=100, description="Name of the person who processed the request")
