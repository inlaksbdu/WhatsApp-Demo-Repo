from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from src.config.database import get_db
from .service import ConversationService
from .schemas.response import (
    ConversationResponse,
    TotalChatsResponse,
    ActiveChatsResponse,
    ChatHoursResponse,
    LanguageDistributionResponse,
    ProspectUserStats,
    PaginatedConversationResponse,
    ExistingUserStats
)
from .schemas.request import ConversationFilter, CustomerType, DateRangeFilter, UserSearchFilter, ChatHistoryFilter
from enum import Enum

router = APIRouter(prefix="/conversations", tags=["conversations"])

@router.get("/total", response_model=TotalChatsResponse)
async def get_total_chats(db: Session = Depends(get_db)):
    """
    Get the total number of conversations in the database
    """
    total = await ConversationService.get_total_chats(db)
    return {"total_chats": total}

@router.get("/active", response_model=ActiveChatsResponse)
async def get_active_chats(
    hours: int = Query(24, ge=1, le=168, description="Hours to consider for active chats"),
    db: Session = Depends(get_db)
):
    """
    Get the number of active conversations in the last specified hours
    """
    active = await ConversationService.get_active_chats(db, hours)
    return {"active_chats": active}

@router.get("/hours-distribution", response_model=ChatHoursResponse)
async def get_chat_hours_distribution(db: Session = Depends(get_db)):
    """
    Get the distribution of chats by hour of day, including most and least active hours
    """
    return await ConversationService.get_chat_hours_distribution(db)

@router.get("/language-distribution", response_model=LanguageDistributionResponse)
async def get_language_distribution(db: Session = Depends(get_db)):
    """
    Get the distribution of conversations by detected language
    """
    languages = await ConversationService.get_language_distribution(db)
    return {"languages": languages}

@router.get("/existing-users/by-name", response_model=List[ExistingUserStats])
async def get_existing_users_by_name(
    name: str = Query(..., description="Name to search for"),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get existing users by name with pagination
    """
    users = await ConversationService.get_existing_users_by_name(db, name, limit)
    return users

@router.get("/existing-users/by-number", response_model=List[ExistingUserStats])
async def get_existing_users_by_number(
    phone_number: str = Query(..., description="Phone number to search for"),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get existing users by phone number with pagination
    """
    users = await ConversationService.get_existing_users_by_number(db, phone_number, limit)
    return users

@router.get("/prospect-users/by-number", response_model=List[ProspectUserStats])
async def get_prospect_users_by_number(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get prospect users sorted by phone number with their chat statistics
    """
    return await ConversationService.get_prospect_users_by_number(db, limit)

@router.get("/", response_model=PaginatedConversationResponse)
async def get_conversations(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    customer_type: Optional[str] = None,
    sentiment: Optional[str] = None,
    language: Optional[str] = None,
    phone_number: Optional[str] = None,
    customer_name: Optional[str] = None,
    has_transfer: Optional[bool] = None,
    has_bank_statement: Optional[bool] = None,
    day: Optional[date] = None
):
    """
    Get paginated conversations with various filter options
    """
    skip = (page - 1) * size
    
    filters = ConversationFilter(
        start_date=start_date,
        end_date=end_date,
        customer_type=customer_type,
        sentiment=sentiment,
        language=language,
        phone_number=phone_number,
        customer_name=customer_name,
        has_transfer=has_transfer,
        has_bank_statement=has_bank_statement,
        day=day
    )
    
    conversations, total = await ConversationService.get_conversations(
        db, filters, skip, size
    )
    
    pages = (total + size - 1) // size
    
    return PaginatedConversationResponse(
        items=conversations,
        total=total,
        page=page,
        size=size,
        pages=pages
    )

@router.post("/existing-users/search", response_model=List[ExistingUserStats])
async def search_existing_users(
    filter: UserSearchFilter,
    db: Session = Depends(get_db)
):
    """
    Search existing users by name or phone number with optional date filtering
    """
    return await ConversationService.get_existing_users_by_filter(db, filter)

@router.post("/prospect-users/search", response_model=List[ProspectUserStats])
async def search_prospect_users(
    filter: UserSearchFilter,
    db: Session = Depends(get_db)
):
    """
    Search prospect users by phone number with optional date filtering
    """
    return await ConversationService.get_prospect_users_by_filter(db, filter)

@router.post("/existing-users/chat-history", response_model=PaginatedConversationResponse)
async def get_existing_user_chat_history(
    filter: ChatHistoryFilter,
    db: Session = Depends(get_db)
):
    """
    Get chat history for an existing user by name or phone number
    """
    conversations, total = await ConversationService.get_user_chat_history(
        db, filter, CustomerType.CUSTOMER
    )
    
    pages = (total + filter.size - 1) // filter.size
    
    return PaginatedConversationResponse(
        items=conversations,
        total=total,
        page=filter.page,
        size=filter.size,
        pages=pages
    )

@router.post("/prospect-users/chat-history", response_model=PaginatedConversationResponse)
async def get_prospect_user_chat_history(
    filter: ChatHistoryFilter,
    db: Session = Depends(get_db)
):
    """
    Get chat history for a prospect user by phone number
    """
    conversations, total = await ConversationService.get_user_chat_history(
        db, filter, CustomerType.PROSPECT
    )
    
    pages = (total + filter.size - 1) // filter.size
    
    return PaginatedConversationResponse(
        items=conversations,
        total=total,
        page=filter.page,
        size=filter.size,
        pages=pages
    ) 