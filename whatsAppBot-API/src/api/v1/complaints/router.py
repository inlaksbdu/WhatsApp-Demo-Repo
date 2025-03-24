from fastapi import APIRouter, Depends, Query, HTTPException, Path, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from src.config.database import get_db
from .service import ComplaintService
from .schemas.request import (
    ComplainStatus,
    ComplaintFilter,
    UpdateComplaintStatusRequest,
    HoldComplaintRequest,
    RejectComplaintRequest,
    ResolveComplaintRequest
)
from .schemas.response import (
    ComplaintResponse,
    PaginatedComplaintResponse,
    ComplaintStatusUpdateResponse
)

router = APIRouter(prefix="/complaints", tags=["complaints"])

@router.get("/", response_model=PaginatedComplaintResponse)
async def get_complaints(
    name: Optional[str] = None,
    email: Optional[str] = None,
    phone_number: Optional[str] = None,
    complaint_type: Optional[str] = None,
    status: Optional[ComplainStatus] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get all complaints with optional filtering and pagination
    """
    skip = (page - 1) * size
    
    filters = ComplaintFilter(
        name=name,
        email=email,
        phone_number=phone_number,
        complaint_type=complaint_type,
        status=status,
        start_date=start_date,
        end_date=end_date
    )
    
    complaints, total = await ComplaintService.get_complaints(db, filters, skip, size)
    
    pages = (total + size - 1) // size
    
    return PaginatedComplaintResponse(
        items=complaints,
        total=total,
        page=page,
        size=size,
        pages=pages
    )

@router.get("/{complaint_id}", response_model=ComplaintResponse)
async def get_complaint_by_id(
    complaint_id: int = Path(..., ge=1),
    db: Session = Depends(get_db)
):
    """
    Get a specific complaint by ID
    """
    complaint = await ComplaintService.get_complaint_by_id(db, complaint_id)
    
    if not complaint:
        raise HTTPException(
            status_code=404,
            detail=f"Complaint with ID {complaint_id} not found"
        )
    
    return complaint

@router.patch("/{complaint_id}/status", response_model=ComplaintStatusUpdateResponse)
async def update_complaint_status(
    complaint_id: int = Path(..., ge=1),
    status_update: UpdateComplaintStatusRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    Update the status of a complaint
    """
    complaint = await ComplaintService.update_complaint_status(db, complaint_id, status_update)
    
    if not complaint:
        raise HTTPException(
            status_code=404,
            detail=f"Complaint with ID {complaint_id} not found"
        )
    
    return ComplaintStatusUpdateResponse(
        id=complaint.id,
        status=complaint.status,
        message=f"Complaint status updated to {complaint.status}"
    )

@router.post("/{complaint_id}/hold", response_model=ComplaintResponse)
async def hold_complaint(
    complaint_id: int = Path(..., ge=1),
    hold_request: HoldComplaintRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    Put a complaint on hold with a reason
    """
    complaint = await ComplaintService.hold_complaint(db, complaint_id, hold_request)
    
    if not complaint:
        raise HTTPException(
            status_code=404,
            detail=f"Complaint with ID {complaint_id} not found"
        )
    
    return complaint

@router.post("/{complaint_id}/reject", response_model=ComplaintResponse)
async def reject_complaint(
    complaint_id: int = Path(..., ge=1),
    reject_request: RejectComplaintRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    Reject a complaint with a reason
    """
    complaint = await ComplaintService.reject_complaint(db, complaint_id, reject_request)
    
    if not complaint:
        raise HTTPException(
            status_code=404,
            detail=f"Complaint with ID {complaint_id} not found"
        )
    
    return complaint

@router.post("/{complaint_id}/resolve", response_model=ComplaintResponse)
async def resolve_complaint(
    complaint_id: int = Path(..., ge=1),
    resolve_request: ResolveComplaintRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    Resolve a complaint with notes and resolver information
    """
    complaint = await ComplaintService.resolve_complaint(db, complaint_id, resolve_request)
    
    if not complaint:
        raise HTTPException(
            status_code=404,
            detail=f"Complaint with ID {complaint_id} not found"
        )
    
    return complaint
