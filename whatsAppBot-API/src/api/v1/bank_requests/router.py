from fastapi import APIRouter, Depends, Query, HTTPException, Path, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from src.config.database import get_db
from .service import BankRequestService
from .schemas.request import (
    RequestStatus,
    BankRequestFilter,
    UpdateRequestStatusRequest,
    RejectRequestRequest,
    ResolveRequestRequest
)
from .schemas.response import (
    BankRequestResponse,
    PaginatedBankRequestResponse,
    RequestStatusUpdateResponse
)

router = APIRouter(prefix="/bank-requests", tags=["bank-requests"])

@router.get("/", response_model=PaginatedBankRequestResponse)
async def get_bank_requests(
    email: Optional[str] = None,
    customer_name: Optional[str] = None,
    reference_code: Optional[str] = None,
    service_type: Optional[str] = None,
    status: Optional[RequestStatus] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get all bank requests with optional filtering and pagination
    """
    skip = (page - 1) * size
    
    filters = BankRequestFilter(
        email=email,
        customer_name=customer_name,
        reference_code=reference_code,
        service_type=service_type,
        status=status,
        start_date=start_date,
        end_date=end_date
    )
    
    requests, total = await BankRequestService.get_bank_requests(db, filters, skip, size)
    
    pages = (total + size - 1) // size
    
    return PaginatedBankRequestResponse(
        items=requests,
        total=total,
        page=page,
        size=size,
        pages=pages
    )

@router.get("/{request_id}", response_model=BankRequestResponse)
async def get_bank_request_by_id(
    request_id: int = Path(..., ge=1),
    db: Session = Depends(get_db)
):
    """
    Get a specific bank request by ID
    """
    bank_request = await BankRequestService.get_bank_request_by_id(db, request_id)
    
    if not bank_request:
        raise HTTPException(
            status_code=404,
            detail=f"Bank request with ID {request_id} not found"
        )
    
    return bank_request

@router.patch("/{request_id}/status", response_model=RequestStatusUpdateResponse)
async def update_request_status(
    request_id: int = Path(..., ge=1),
    status_update: UpdateRequestStatusRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    Update the status of a bank request
    """
    bank_request = await BankRequestService.update_request_status(db, request_id, status_update)
    
    if not bank_request:
        raise HTTPException(
            status_code=404,
            detail=f"Bank request with ID {request_id} not found"
        )
    
    return RequestStatusUpdateResponse(
        id=bank_request.id,
        status=bank_request.status,
        message=f"Bank request status updated to {bank_request.status}"
    )

@router.post("/{request_id}/reject", response_model=BankRequestResponse)
async def reject_request(
    request_id: int = Path(..., ge=1),
    reject_request: RejectRequestRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    Reject a bank request with a reason
    """
    bank_request = await BankRequestService.reject_request(db, request_id, reject_request)
    
    if not bank_request:
        raise HTTPException(
            status_code=404,
            detail=f"Bank request with ID {request_id} not found"
        )
    
    return bank_request

@router.post("/{request_id}/resolve", response_model=BankRequestResponse)
async def resolve_request(
    request_id: int = Path(..., ge=1),
    resolve_request: ResolveRequestRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    Resolve a bank request with processing notes and processor information
    """
    bank_request = await BankRequestService.resolve_request(db, request_id, resolve_request)
    
    if not bank_request:
        raise HTTPException(
            status_code=404,
            detail=f"Bank request with ID {request_id} not found"
        )
    
    return bank_request
