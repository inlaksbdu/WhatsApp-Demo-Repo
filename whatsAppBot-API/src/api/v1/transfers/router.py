from fastapi import APIRouter, Depends, Query, HTTPException, Path, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from src.config.database import get_db
from .service import TransferService
from .schemas.request import TransferFilter, TransferStatus, TimeRangeRequest
from .schemas.response import (
    TransferResponse,
    TransferCount,
    CustomerTransferHistory,
    PaginatedTransferResponse,
    TransferPeriodAnalysis
)

router = APIRouter(prefix="/transfers", tags=["transfers"])

@router.post("/count", response_model=TransferCount)
async def get_transfer_count(
    time_range: TimeRangeRequest,
    db: Session = Depends(get_db)
):
    """
    Get the count and statistics of transfers within a specific time range
    """
    if time_range.end_date < time_range.start_date:
        raise HTTPException(
            status_code=400,
            detail="End date must be after start date"
        )
        
    result = await TransferService.get_transfer_count(
        db, time_range.start_date, time_range.end_date
    )
    
    return result

@router.get("/customers/most-active", response_model=List[CustomerTransferHistory])
async def get_customers_with_most_transfers(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get customers with the most transfer history
    """
    customers = await TransferService.get_customers_with_most_transfers(db, limit)
    return customers

@router.get("/customer/by-name/{customer_name}", response_model=PaginatedTransferResponse)
async def get_customer_transfers_by_name(
    customer_name: str = Path(..., min_length=1),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get transfer details for a specific customer by name within a time range
    """
    skip = (page - 1) * size
    
    transfers, total = await TransferService.get_customer_transfers_by_name(
        db, customer_name, start_date, end_date, skip, size
    )
    
    pages = (total + size - 1) // size
    
    return PaginatedTransferResponse(
        items=transfers,
        total=total,
        page=page,
        size=size,
        pages=pages
    )

@router.get("/customer/by-number/{phone_number}", response_model=PaginatedTransferResponse)
async def get_customer_transfers_by_number(
    phone_number: str = Path(..., min_length=1),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get transfer details for a specific customer by phone number within a time range
    """
    skip = (page - 1) * size
    
    transfers, total = await TransferService.get_customer_transfers_by_number(
        db, phone_number, start_date, end_date, skip, size
    )
    
    pages = (total + size - 1) // size
    
    return PaginatedTransferResponse(
        items=transfers,
        total=total,
        page=page,
        size=size,
        pages=pages
    )

@router.get("/periods/analysis", response_model=List[TransferPeriodAnalysis])
async def analyze_transfer_periods(
    period_type: str = Query(
        "hour", 
        description="Type of period analysis (hour, day_of_week, month, day)"
    ),
    db: Session = Depends(get_db)
):
    """
    Analyze when transfers happen most frequently
    Options: hour (hour of day), day_of_week, month, day (specific dates)
    """
    valid_period_types = ["hour", "day_of_week", "month", "day"]
    
    if period_type not in valid_period_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid period type. Must be one of: {', '.join(valid_period_types)}"
        )
    
    results = await TransferService.analyze_transfer_periods(db, period_type)
    return results
