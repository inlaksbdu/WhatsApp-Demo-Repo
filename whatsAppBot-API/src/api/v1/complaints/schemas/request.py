from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
from datetime import datetime

class ComplainStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ON_HOLD = "on_hold"
    REJECTED = "rejected"

class ComplaintFilter(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    complaint_type: Optional[str] = None
    status: Optional[ComplainStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class UpdateComplaintStatusRequest(BaseModel):
    status: ComplainStatus = Field(..., description="New status for the complaint")

class HoldComplaintRequest(BaseModel):
    hold_reason: str = Field(..., min_length=5, max_length=500, description="Reason for putting the complaint on hold")

class RejectComplaintRequest(BaseModel):
    rejection_reason: str = Field(..., min_length=5, max_length=500, description="Reason for rejecting the complaint")

class ResolveComplaintRequest(BaseModel):
    resolution_notes: str = Field(..., min_length=5, max_length=1000, description="Notes about how the complaint was resolved")
    resolved_by: str = Field(..., min_length=2, max_length=100, description="Name of the person who resolved the complaint")
