from fastapi import APIRouter, Depends, Query, HTTPException, Path
from sqlalchemy.orm import Session
from typing import List, Optional
from src.config.database import get_db
from .service import CustomerService
from .schemas.request import CustomerType, CustomerFilter, CustomerDetailRequest
from .schemas.response import (
    CustomerCount,
    CustomerEngagement,
    CustomerSentiment,
    Customer360View,
    PlatformChannel
)

router = APIRouter(prefix="/customers", tags=["customers"])

@router.get("/count", response_model=CustomerCount)
async def get_customer_count(db: Session = Depends(get_db)):
    """
    Get the total count of customers, broken down by type (prospect vs existing)
    """
    counts = await CustomerService.get_customer_count(db)
    return counts

@router.get("/most-engaged", response_model=List[CustomerEngagement])
async def get_most_engaged_customers(
    customer_type: Optional[CustomerType] = None,
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get customers with the most engagement (conversation count)
    Optionally filter by customer type (PROSPECT or CUSTOMER)
    """
    customers = await CustomerService.get_most_engaged_customers(db, customer_type, limit)
    return customers

@router.get("/most-engaged/prospects", response_model=List[CustomerEngagement])
async def get_most_engaged_prospects(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get prospect customers with the most engagement (conversation count)
    """
    customers = await CustomerService.get_most_engaged_customers(
        db, CustomerType.PROSPECT, limit
    )
    return customers

@router.get("/most-engaged/existing", response_model=List[CustomerEngagement])
async def get_most_engaged_existing_customers(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get existing customers with the most engagement (conversation count)
    """
    customers = await CustomerService.get_most_engaged_customers(
        db, CustomerType.CUSTOMER, limit
    )
    return customers

@router.get("/most-positive-sentiment", response_model=List[CustomerSentiment])
async def get_customers_with_most_positive_sentiment(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get customers with the most positive sentiment
    """
    customers = await CustomerService.get_customers_by_sentiment(db, positive=True, limit=limit)
    return customers

@router.get("/most-negative-sentiment", response_model=List[CustomerSentiment])
async def get_customers_with_most_negative_sentiment(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get customers with the most negative sentiment
    """
    customers = await CustomerService.get_customers_by_sentiment(db, positive=False, limit=limit)
    return customers

@router.get("/360-view", response_model=Customer360View)
async def get_customer_360_view(
    name: Optional[str] = None,
    phone_number: Optional[str] = None,
    customer_type: Optional[CustomerType] = None,
    db: Session = Depends(get_db)
):
    """
    Get comprehensive 360 view of a customer by name or phone number
    """
    if not name and not phone_number:
        raise HTTPException(
            status_code=400, 
            detail="Either name or phone_number must be provided"
        )
    
    request = CustomerDetailRequest(
        name=name,
        phone_number=phone_number,
        customer_type=customer_type
    )
    
    customer = await CustomerService.get_customer_360_view(db, request)
    
    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )
    
    return customer

@router.get("/360-view/existing", response_model=Customer360View)
async def get_existing_customer_360_view(
    name: Optional[str] = None,
    phone_number: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get comprehensive 360 view of an existing customer by name or phone number
    """
    if not name and not phone_number:
        raise HTTPException(
            status_code=400, 
            detail="Either name or phone_number must be provided"
        )
    
    request = CustomerDetailRequest(
        name=name,
        phone_number=phone_number,
        customer_type=CustomerType.CUSTOMER
    )
    
    customer = await CustomerService.get_customer_360_view(db, request)
    
    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Existing customer not found"
        )
    
    return customer

@router.get("/360-view/prospect", response_model=Customer360View)
async def get_prospect_customer_360_view(
    name: Optional[str] = None,
    phone_number: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get comprehensive 360 view of a prospect customer by name or phone number
    """
    if not name and not phone_number:
        raise HTTPException(
            status_code=400, 
            detail="Either name or phone_number must be provided"
        )
    
    request = CustomerDetailRequest(
        name=name,
        phone_number=phone_number,
        customer_type=CustomerType.PROSPECT
    )
    
    customer = await CustomerService.get_customer_360_view(db, request)
    
    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Prospect customer not found"
        )
    
    return customer

@router.get("/platform-channel/{phone_number}", response_model=PlatformChannel)
async def get_platform_channel(
    phone_number: str = Path(..., description="Customer phone number"),
    db: Session = Depends(get_db)
):
    """
    Determine the communication channel for a customer (WhatsApp or Other)
    """
    result = await CustomerService.get_platform_channel(db, phone_number)
    
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"No customer found with phone number: {phone_number}"
        )
    
    return result 