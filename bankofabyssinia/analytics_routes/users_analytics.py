from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
import pytz
from sqlalchemy import distinct, extract, func, text
from sqlalchemy.orm import Session
from models.database import Complaint, Conversation, get_db
import logging

from services.analytics import ChatMetrics, ComplaintMetrics, ConversationHistory, PhoneNumberOverview, ProfileSummary, UserChatPattern, UserComplaintPattern, UserProfile, UserStats, VolumeStats

router = APIRouter(
    prefix="/user-analytics",
    tags=["User Analytics"]
)

# User listing endpoints
@router.get("/users/list/all", response_model=List[UserStats])
async def get_all_users(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    Get list of all unique users who have interacted with the bot
    """
    users = db.query(
        Conversation.phone_number,
        Conversation.whatsapp_profile_name,
        Conversation.customer_type,
        func.count(Conversation.id).label('total_messages'),
        func.max(Conversation.created_at).label('last_activity'),
        func.min(Conversation.created_at).label('first_interaction')
    ).group_by(
        Conversation.phone_number,
        Conversation.whatsapp_profile_name,
        Conversation.customer_type
    ).offset(skip).limit(limit).all()

    return [
        UserStats(
            phone_number=user.phone_number,
            whatsapp_profile_name=user.whatsapp_profile_name,
            customer_type=user.customer_type,
            total_messages=user.total_messages,
            last_activity=user.last_activity,
            first_interaction=user.first_interaction
        ) for user in users
    ]

@router.get("/users/list/prospects", response_model=List[UserStats])
async def get_prospect_users(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    Get list of all prospect users
    """
    prospects = db.query(
        Conversation.phone_number,
        Conversation.whatsapp_profile_name,
        Conversation.customer_type,
        func.count(Conversation.id).label('total_messages'),
        func.max(Conversation.created_at).label('last_activity'),
        func.min(Conversation.created_at).label('first_interaction')
    ).filter(
        Conversation.customer_type == 'PROSPECT'
    ).group_by(
        Conversation.phone_number,
        Conversation.whatsapp_profile_name,
        Conversation.customer_type
    ).offset(skip).limit(limit).all()

    return [UserStats.from_orm(prospect) for prospect in prospects]

@router.get("/users/list/existing", response_model=List[UserStats])
async def get_existing_users(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    Get list of all existing customers
    """
    customers = db.query(
        Conversation.phone_number,
        Conversation.whatsapp_profile_name,
        Conversation.customer_type,
        func.count(Conversation.id).label('total_messages'),
        func.max(Conversation.created_at).label('last_activity'),
        func.min(Conversation.created_at).label('first_interaction')
    ).filter(
        Conversation.customer_type == 'EXISTING'
    ).group_by(
        Conversation.phone_number,
        Conversation.whatsapp_profile_name,
        Conversation.customer_type
    ).offset(skip).limit(limit).all()

    return [UserStats.from_orm(customer) for customer in customers]

@router.get("/users/active", response_model=List[UserStats])
async def get_active_users(
    hours: int = Query(default=24, description="Hours to consider for active users"),
    db: Session = Depends(get_db)
):
    """
    Get users active within the specified time window
    """
    cutoff_time = datetime.now(pytz.UTC) - timedelta(hours=hours)
    
    active_users = db.query(
        Conversation.phone_number,
        Conversation.whatsapp_profile_name,
        Conversation.customer_type,
        func.count(Conversation.id).label('total_messages'),
        func.max(Conversation.created_at).label('last_activity'),
        func.min(Conversation.created_at).label('first_interaction')
    ).filter(
        Conversation.created_at >= cutoff_time
    ).group_by(
        Conversation.phone_number,
        Conversation.whatsapp_profile_name,
        Conversation.customer_type
    ).all()

    return [UserStats.from_orm(user) for user in active_users]

@router.get("/users/search")
async def search_users(
    query: str = Query(..., min_length=3),
    db: Session = Depends(get_db)
):
    """
    Search users by WhatsApp name or phone number
    """
    search_results = db.query(
        Conversation.phone_number,
        Conversation.whatsapp_profile_name,
        Conversation.customer_type,
        func.count(Conversation.id).label('total_messages'),
        func.max(Conversation.created_at).label('last_activity'),
        func.min(Conversation.created_at).label('first_interaction')
    ).filter(
        (Conversation.whatsapp_profile_name.ilike(f"%{query}%")) |
        (Conversation.phone_number.ilike(f"%{query}%"))
    ).group_by(
        Conversation.phone_number,
        Conversation.whatsapp_profile_name,
        Conversation.customer_type
    ).all()

    return [UserStats.from_orm(user) for user in search_results]

@router.get("/users/conversations/{phone_number}", response_model=List[ConversationHistory])
async def get_user_conversations(
    phone_number: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """
    Get conversation history for a specific user
    """
    query = db.query(Conversation).filter(Conversation.phone_number == phone_number)
    
    if start_date:
        query = query.filter(Conversation.created_at >= start_date)
    if end_date:
        query = query.filter(Conversation.created_at <= end_date)
    
    conversations = query.order_by(Conversation.created_at.desc()).all()
    
    return [
        ConversationHistory(
            message=conv.message,
            response=conv.response,
            created_at=conv.created_at
        ) for conv in conversations
    ]

@router.get("/users/profile-summary/{phone_number}", response_model=ProfileSummary)
async def get_user_profile_summary(
    phone_number: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed interaction summary for a specific user
    """
    # Get basic stats
    stats = db.query(
        func.count(Conversation.id).label('total_conversations'),
        func.min(Conversation.created_at).label('first_interaction'),
        func.max(Conversation.created_at).label('last_interaction'),
        Conversation.customer_type
    ).filter(
        Conversation.phone_number == phone_number
    ).group_by(Conversation.customer_type).first()

    if not stats:
        raise HTTPException(status_code=404, detail="User not found")

    # Calculate average daily messages
    days_since_first = (stats.last_interaction - stats.first_interaction).days or 1
    avg_daily = stats.total_conversations / days_since_first

    # Find most active hour
    most_active = db.query(
        extract('hour', Conversation.created_at).label('hour'),
        func.count(Conversation.id).label('count')
    ).filter(
        Conversation.phone_number == phone_number
    ).group_by('hour').order_by(text('count DESC')).first()

    return ProfileSummary(
        total_conversations=stats.total_conversations,
        average_daily_messages=round(avg_daily, 2),
        most_active_hour=most_active.hour if most_active else 0,
        customer_type=stats.customer_type,
        first_interaction=stats.first_interaction,
        last_interaction=stats.last_interaction
    )

@router.get("/conversations/volume", response_model=List[VolumeStats])
async def get_conversation_volume(
    db: Session = Depends(get_db),
    days: int = Query(default=7, description="Number of days to analyze")
):
    """
    Get conversation volume metrics grouped by profile/number
    """
    cutoff_date = datetime.now(pytz.UTC) - timedelta(days=days)
    
    # Modified query to return results in a format that can be serialized
    volume_stats = db.query(
        Conversation.whatsapp_profile_name,
        Conversation.phone_number,
        func.date(Conversation.created_at).label('date'),
        func.count(Conversation.id).label('message_count')
    ).filter(
        Conversation.created_at >= cutoff_date
    ).group_by(
        Conversation.whatsapp_profile_name,
        Conversation.phone_number,
        func.date(Conversation.created_at)
    ).order_by(text('date DESC')).all()

    # Convert SQLAlchemy result objects to Pydantic models
    return [
        VolumeStats(
            whatsapp_profile_name=stat[0],
            phone_number=stat[1],
            date=stat[2],
            message_count=stat[3]
        ) for stat in volume_stats
    ]

# Optional: Add additional endpoint for aggregated daily volumes
class DailyVolume(BaseModel):
    date: datetime
    total_messages: int
    unique_users: int

@router.get("/conversations/daily-volume", response_model=List[DailyVolume])
async def get_daily_conversation_volume(
    db: Session = Depends(get_db),
    days: int = Query(default=7, description="Number of days to analyze")
):
    """
    Get daily conversation volumes with user counts
    """
    cutoff_date = datetime.now(pytz.UTC) - timedelta(days=days)
    
    daily_stats = db.query(
        func.date(Conversation.created_at).label('date'),
        func.count(Conversation.id).label('total_messages'),
        func.count(distinct(Conversation.phone_number)).label('unique_users')
    ).filter(
        Conversation.created_at >= cutoff_date
    ).group_by(
        func.date(Conversation.created_at)
    ).order_by(text('date DESC')).all()

    return [
        DailyVolume(
            date=stat[0],
            total_messages=stat[1],
            unique_users=stat[2]
        ) for stat in daily_stats
    ]


@router.get("/users/conversations/by-name/{whatsapp_name}", response_model=List[ConversationHistory])
async def get_user_conversations_by_name(
    whatsapp_name: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """
    Get conversation history for a user by their WhatsApp profile name
    """
    query = db.query(Conversation).filter(
        Conversation.whatsapp_profile_name.ilike(f"%{whatsapp_name}%")
    )
    
    if start_date:
        query = query.filter(Conversation.created_at >= start_date)
    if end_date:
        query = query.filter(Conversation.created_at <= end_date)
    
    conversations = query.order_by(Conversation.created_at.desc()).all()
    
    if not conversations:
        raise HTTPException(
            status_code=404,
            detail=f"No conversations found for WhatsApp name: {whatsapp_name}"
        )
    
    return [
        ConversationHistory(
            message=conv.message,
            response=conv.response,
            created_at=conv.created_at,
            phone_number=conv.phone_number,
            customer_type=conv.customer_type
        ) for conv in conversations
    ]

@router.get("/users/profile-summary/by-name/{whatsapp_name}", response_model=List[ProfileSummary])
async def get_user_profile_summary_by_name(
    whatsapp_name: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed interaction summary for users matching the WhatsApp profile name
    """
    # First get all matching profiles (since names might not be unique)
    profiles = db.query(
        Conversation.whatsapp_profile_name,
        Conversation.phone_number,
        Conversation.customer_type,
        func.count(Conversation.id).label('total_conversations'),
        func.min(Conversation.created_at).label('first_interaction'),
        func.max(Conversation.created_at).label('last_interaction')
    ).filter(
        Conversation.whatsapp_profile_name.ilike(f"%{whatsapp_name}%")
    ).group_by(
        Conversation.whatsapp_profile_name,
        Conversation.phone_number,
        Conversation.customer_type
    ).all()

    if not profiles:
        raise HTTPException(
            status_code=404,
            detail=f"No profiles found for WhatsApp name: {whatsapp_name}"
        )

    result = []
    for profile in profiles:
        # Calculate average daily messages
        days_since_first = (profile.last_interaction - profile.first_interaction).days or 1
        avg_daily = profile.total_conversations / days_since_first

        # Find most active hour for this profile
        most_active = db.query(
            extract('hour', Conversation.created_at).label('hour'),
            func.count(Conversation.id).label('count')
        ).filter(
            Conversation.whatsapp_profile_name == profile.whatsapp_profile_name,
            Conversation.phone_number == profile.phone_number
        ).group_by('hour').order_by(text('count DESC')).first()

        result.append(ProfileSummary(
            whatsapp_profile_name=profile.whatsapp_profile_name,
            phone_number=profile.phone_number,
            total_conversations=profile.total_conversations,
            average_daily_messages=round(avg_daily, 2),
            most_active_hour=most_active.hour if most_active else 0,
            customer_type=profile.customer_type,
            first_interaction=profile.first_interaction,
            last_interaction=profile.last_interaction
        ))

    return result



# Conversation Analysis Endpoints
@router.get("/analytics/chat/metrics", response_model=ChatMetrics)
async def get_chat_metrics(
    db: Session = Depends(get_db),
    days: int = Query(default=30, ge=1, le=365),
    customer_type: Optional[str] = None
):
    """
    Get metrics purely from chat interactions
    """
    cutoff_date = datetime.now(pytz.UTC) - timedelta(days=days)
    
    query = db.query(
        func.count(Conversation.id).label('total_messages'),
        func.count(distinct(Conversation.phone_number)).label('unique_users')
    ).filter(Conversation.created_at >= cutoff_date)
    
    if customer_type:
        query = query.filter(Conversation.customer_type == customer_type)
    
    base_metrics = query.first()
    
    # Get customer type distribution
    type_dist = db.query(
        Conversation.customer_type,
        func.count(distinct(Conversation.phone_number)).label('count')
    ).filter(
        Conversation.created_at >= cutoff_date
    ).group_by(Conversation.customer_type).all()
    
    # Get active hours
    hour_dist = db.query(
        func.extract('hour', Conversation.created_at).label('hour'),
        func.count(Conversation.id).label('count')
    ).filter(
        Conversation.created_at >= cutoff_date
    ).group_by('hour').order_by(text('count DESC')).limit(5).all()
    
    return ChatMetrics(
        total_messages=base_metrics.total_messages,
        unique_users=base_metrics.unique_users,
        avg_messages_per_user=base_metrics.total_messages / base_metrics.unique_users if base_metrics.unique_users > 0 else 0,
        customer_type_distribution={t.customer_type: t.count for t in type_dist},
        most_active_hours=[{"hour": h.hour, "count": h.count} for h in hour_dist]
    )

@router.get("/analytics/chat/user-patterns/{phone_number}", response_model=UserChatPattern)
async def get_chat_patterns(
    phone_number: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed chat patterns for a specific phone number
    """
    user_data = db.query(
        Conversation.whatsapp_profile_name,
        Conversation.phone_number,
        Conversation.customer_type,
        func.count(Conversation.id).label('total_messages'),
        func.min(Conversation.created_at).label('first_message'),
        func.max(Conversation.created_at).label('last_message'),
        func.count(distinct(func.date(Conversation.created_at))).label('active_days')
    ).filter(
        Conversation.phone_number == phone_number
    ).group_by(
        Conversation.whatsapp_profile_name,
        Conversation.phone_number,
        Conversation.customer_type
    ).first()
    
    if not user_data:
        raise HTTPException(status_code=404, detail="No chat history found for this number")
    
    days_difference = (user_data.last_message - user_data.first_message).days or 1
    
    return UserChatPattern(
        whatsapp_profile_name=user_data.whatsapp_profile_name,
        phone_number=user_data.phone_number,
        customer_type=user_data.customer_type,
        total_messages=user_data.total_messages,
        first_message=user_data.first_message,
        last_message=user_data.last_message,
        average_messages_per_day=user_data.total_messages / days_difference,
        active_days=user_data.active_days
    )

# Complaint Analysis Endpoints
@router.get("/analytics/complaints/metrics", response_model=ComplaintMetrics)
async def get_complaint_metrics(
    db: Session = Depends(get_db),
    days: int = Query(default=30, ge=1, le=365),
    status: Optional[str] = None
):
    """
    Get metrics purely from complaint data
    """
    cutoff_date = datetime.now(pytz.UTC) - timedelta(days=days)
    
    query = db.query(
        func.count(Complaint.id).label('total_complaints'),
        func.count(distinct(Complaint.phone_number)).label('unique_users')
    ).filter(Complaint.created_at >= cutoff_date)
    
    if status:
        query = query.filter(Complaint.status == status)
    
    base_metrics = query.first()
    
    # Get complaint type distribution
    type_dist = db.query(
        Complaint.complaint_type,
        func.count(Complaint.id).label('count')
    ).filter(
        Complaint.created_at >= cutoff_date
    ).group_by(Complaint.complaint_type).all()
    
    # Get status distribution
    status_dist = db.query(
        Complaint.status,
        func.count(Complaint.id).label('count')
    ).filter(
        Complaint.created_at >= cutoff_date
    ).group_by(Complaint.status).all()
    
    # Calculate average resolution time for resolved complaints
    avg_resolution = db.query(
        func.avg(func.extract('epoch', Complaint.updated_at - Complaint.created_at))
    ).filter(
        Complaint.created_at >= cutoff_date,
        Complaint.status == 'RESOLVED'
    ).scalar()
    
    return ComplaintMetrics(
        total_complaints=base_metrics.total_complaints,
        unique_users=base_metrics.unique_users,
        complaint_type_distribution={t.complaint_type: t.count for t in type_dist},
        status_distribution={s.status: s.count for s in status_dist},
        avg_resolution_time=avg_resolution
    )

@router.get("/analytics/complaints/user-patterns/{phone_number}", response_model=UserComplaintPattern)
async def get_complaint_patterns(
    phone_number: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed complaint patterns for a specific phone number
    """
    user_data = db.query(
        Complaint.name,
        Complaint.phone_number,
        func.count(Complaint.id).label('total_complaints'),
        func.min(Complaint.created_at).label('first_complaint'),
        func.max(Complaint.created_at).label('last_complaint')
    ).filter(
        Complaint.phone_number == phone_number
    ).group_by(
        Complaint.name,
        Complaint.phone_number
    ).first()
    
    if not user_data:
        raise HTTPException(status_code=404, detail="No complaints found for this number")
    
    # Get list of complaint types and statuses
    complaint_details = db.query(
        Complaint.complaint_type,
        Complaint.status
    ).filter(
        Complaint.phone_number == phone_number
    ).all()
    
    return UserComplaintPattern(
        name=user_data.name,
        phone_number=user_data.phone_number,
        total_complaints=user_data.total_complaints,
        complaint_types=list(set(c.complaint_type for c in complaint_details)),
        current_status=list(set(c.status for c in complaint_details)),
        first_complaint=user_data.first_complaint,
        last_complaint=user_data.last_complaint
    )

# Combined Overview Endpoint (with clear separation)
@router.get("/analytics/user-overview/{phone_number}", response_model=PhoneNumberOverview)
async def get_user_overview(
    phone_number: str,
    db: Session = Depends(get_db)
):
    """
    Get overview of both chat and complaint data for a phone number (if exists in either system)
    """
    try:
        chat_data = await get_chat_patterns(phone_number, db)
    except HTTPException:
        chat_data = None
    
    try:
        complaint_data = await get_complaint_patterns(phone_number, db)
    except HTTPException:
        complaint_data = None
    
    return PhoneNumberOverview(
        phone_number=phone_number,
        chat_data=chat_data,
        complaint_data=complaint_data,
        is_linked=bool(chat_data and complaint_data)
    )

@router.get("/users/list", response_model=List[UserProfile])
async def get_user_list(
    db: Session = Depends(get_db),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    customer_type: Optional[str] = None
):
    """
    Get unique users with their WhatsApp names and phone numbers
    """
    query = db.query(
        Conversation.whatsapp_profile_name,
        Conversation.phone_number,
        Conversation.customer_type,
        func.max(Conversation.created_at).label('last_seen'),
        func.count(Conversation.id).label('total_conversations')
    ).group_by(
        Conversation.whatsapp_profile_name,
        Conversation.phone_number,
        Conversation.customer_type
    )
    
    # Apply customer type filter if provided
    if customer_type:
        query = query.filter(Conversation.customer_type == customer_type)
    
    # Order by most recent activity
    query = query.order_by(func.max(Conversation.created_at).desc())
    
    # Apply pagination
    users = query.offset(skip).limit(limit).all()
    
    return [
        UserProfile(
            whatsapp_profile_name=user.whatsapp_profile_name,
            phone_number=user.phone_number,
            customer_type=user.customer_type,
            last_seen=user.last_seen,
            total_conversations=user.total_conversations
        ) for user in users
    ]