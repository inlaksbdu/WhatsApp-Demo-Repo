from fastapi import APIRouter, Depends, Query, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from src.config.database import get_db
from .service import SentimentService
from .schemas.request import (
    SentimentType, 
    CustomerType, 
    SentimentFilter,
    WordAnalysisRequest
)
from .schemas.response import (
    SentimentCount,
    SentimentWordAnalysis,
    CustomerSentimentPolarity
)

router = APIRouter(prefix="/sentiment", tags=["sentiment"])

@router.get("/counts", response_model=SentimentCount)
async def get_sentiment_counts(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    customer_type: Optional[CustomerType] = None,
    db: Session = Depends(get_db)
):
    """
    Get counts of conversations by sentiment type (positive, negative, neutral)
    """
    filter = SentimentFilter(
        start_date=start_date,
        end_date=end_date,
        customer_type=customer_type
    )
    
    counts = await SentimentService.get_sentiment_counts(db, filter)
    return counts

@router.post("/word-analysis", response_model=SentimentWordAnalysis)
async def analyze_sentiment_words(
    request: WordAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Analyze most frequent words in conversations with specific sentiment.
    Can be filtered by customer name or phone number.
    """
    if not request.customer_name and not request.phone_number:
        # If no customer identifiers provided, analyze all conversations
        pass
        
    result = await SentimentService.analyze_sentiment_words(db, request)
    return result

@router.get("/positive-words/by-name/{customer_name}", response_model=SentimentWordAnalysis)
async def get_positive_words_by_name(
    customer_name: str,
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get most frequent words in positive sentiment conversations for a specific customer by name
    """
    request = WordAnalysisRequest(
        customer_name=customer_name,
        sentiment_type=SentimentType.POSITIVE,
        limit=limit
    )
    
    result = await SentimentService.analyze_sentiment_words(db, request)
    return result

@router.get("/positive-words/by-number/{phone_number}", response_model=SentimentWordAnalysis)
async def get_positive_words_by_number(
    phone_number: str,
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get most frequent words in positive sentiment conversations for a specific customer by phone number
    """
    request = WordAnalysisRequest(
        phone_number=phone_number,
        sentiment_type=SentimentType.POSITIVE,
        limit=limit
    )
    
    result = await SentimentService.analyze_sentiment_words(db, request)
    return result

@router.get("/negative-words/by-name/{customer_name}", response_model=SentimentWordAnalysis)
async def get_negative_words_by_name(
    customer_name: str,
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get most frequent words in negative sentiment conversations for a specific customer by name
    """
    request = WordAnalysisRequest(
        customer_name=customer_name,
        sentiment_type=SentimentType.NEGATIVE,
        limit=limit
    )
    
    result = await SentimentService.analyze_sentiment_words(db, request)
    return result

@router.get("/negative-words/by-number/{phone_number}", response_model=SentimentWordAnalysis)
async def get_negative_words_by_number(
    phone_number: str,
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get most frequent words in negative sentiment conversations for a specific customer by phone number
    """
    request = WordAnalysisRequest(
        phone_number=phone_number,
        sentiment_type=SentimentType.NEGATIVE,
        limit=limit
    )
    
    result = await SentimentService.analyze_sentiment_words(db, request)
    return result

@router.get("/high-positive-polarity", response_model=List[CustomerSentimentPolarity])
async def get_users_with_high_positive_polarity(
    customer_type: Optional[CustomerType] = None,
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get users with highest positive sentiment polarity
    Optionally filter by customer type (PROSPECT or CUSTOMER)
    """
    users = await SentimentService.get_users_by_sentiment_polarity(
        db, positive=True, customer_type=customer_type, limit=limit
    )
    return users

@router.get("/high-negative-polarity", response_model=List[CustomerSentimentPolarity])
async def get_users_with_high_negative_polarity(
    customer_type: Optional[CustomerType] = None,
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get users with highest negative sentiment polarity (lowest polarity values)
    Optionally filter by customer type (PROSPECT or CUSTOMER)
    """
    users = await SentimentService.get_users_by_sentiment_polarity(
        db, positive=False, customer_type=customer_type, limit=limit
    )
    return users

@router.get("/high-positive-polarity/prospects", response_model=List[CustomerSentimentPolarity])
async def get_prospects_with_high_positive_polarity(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get prospect users with highest positive sentiment polarity
    """
    users = await SentimentService.get_users_by_sentiment_polarity(
        db, positive=True, customer_type=CustomerType.PROSPECT, limit=limit
    )
    return users

@router.get("/high-positive-polarity/existing", response_model=List[CustomerSentimentPolarity])
async def get_existing_customers_with_high_positive_polarity(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get existing customers with highest positive sentiment polarity
    """
    users = await SentimentService.get_users_by_sentiment_polarity(
        db, positive=True, customer_type=CustomerType.CUSTOMER, limit=limit
    )
    return users

@router.get("/high-negative-polarity/prospects", response_model=List[CustomerSentimentPolarity])
async def get_prospects_with_high_negative_polarity(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get prospect users with highest negative sentiment polarity (lowest polarity values)
    """
    users = await SentimentService.get_users_by_sentiment_polarity(
        db, positive=False, customer_type=CustomerType.PROSPECT, limit=limit
    )
    return users

@router.get("/high-negative-polarity/existing", response_model=List[CustomerSentimentPolarity])
async def get_existing_customers_with_high_negative_polarity(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get existing customers with highest negative sentiment polarity (lowest polarity values)
    """
    users = await SentimentService.get_users_by_sentiment_polarity(
        db, positive=False, customer_type=CustomerType.CUSTOMER, limit=limit
    )
    return users
