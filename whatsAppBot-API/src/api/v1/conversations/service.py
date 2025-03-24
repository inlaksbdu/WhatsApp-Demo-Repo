from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc, case, asc, or_, cast, String
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timedelta
from src.models.models import Conversation, Transfer, BankStatementRequest
from .schemas.request import ConversationFilter, CustomerType, UserSearchFilter, ChatHistoryFilter
from sqlalchemy.sql import extract

class ConversationService:
    @staticmethod
    async def get_total_chats(db: Session) -> int:
        """Get the total number of conversations in the database"""
        return db.query(func.count(Conversation.id)).scalar()
    
    @staticmethod
    async def get_active_chats(db: Session, hours: int = 24) -> int:
        """Get the number of active conversations in the last specified hours"""
        active_cutoff = datetime.utcnow() - timedelta(hours=hours)
        return db.query(func.count(Conversation.id)).filter(
            Conversation.created_at >= active_cutoff
        ).scalar()
    
    @staticmethod
    async def get_chat_hours_distribution(db: Session) -> Dict[str, Any]:
        """Get the distribution of chats by hour of day"""
        # Get chat distribution by hour
        chat_hours = db.query(
            func.extract('hour', Conversation.created_at).label('hour'),
            func.count(Conversation.id).label('count')
        ).group_by('hour').order_by('hour').all()
        
        # Find most and least active hours
        if chat_hours:
            most_active = max(chat_hours, key=lambda x: x[1])
            least_active = min(chat_hours, key=lambda x: x[1])
            most_active_hour = int(most_active[0])
            least_active_hour = int(least_active[0])
        else:
            most_active_hour = None
            least_active_hour = None
        
        return {
            "distribution": [{"hour": int(hour), "count": count} for hour, count in chat_hours],
            "most_active_hour": most_active_hour,
            "least_active_hour": least_active_hour
        }
    
    @staticmethod
    async def get_language_distribution(db: Session) -> List[Dict[str, Any]]:
        """Get the distribution of conversations by detected language"""
        language_dist = db.query(
            Conversation.detected_language.label('language'),
            func.count(Conversation.id).label('count')
        ).group_by(Conversation.detected_language).order_by(desc('count')).all()
        
        return [{"language": lang, "count": count} for lang, count in language_dist]

    # @staticmethod
    # async def get_prospect_users_by_name(
    #     db: Session,
    #     limit: int = 10
    # ) -> List[Dict[str, Any]]:
    #     """Get prospect users sorted by name with their chat statistics"""
    #     return db.query(
    #         Conversation.customer_name,
    #         Conversation.phone_number,
    #         func.count(Conversation.id).label('chat_count'),
    #         func.max(Conversation.created_at).label('last_interaction')
    #     ).filter(
    #         Conversation.customer_type == CustomerType.PROSPECT
    #     ).group_by(
    #         Conversation.customer_name,
    #         Conversation.phone_number
    #     ).order_by(
    #         desc('chat_count')
    #     ).limit(limit).all()
    @staticmethod
    async def get_existing_users_by_name(
        db: Session,
        name: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get existing users filtered by name"""
        query = db.query(
            Conversation.customer_name,
            Conversation.phone_number,
            func.count(Conversation.id).label('chat_count'),
            func.max(Conversation.created_at).label('last_interaction'),
            func.string_agg(
                cast(Conversation.message, String),
                cast(' | ', String)
            ).label('recent_messages')
        ).filter(
            Conversation.customer_type.ilike('EXISTING'),  # Case-insensitive comparison
            Conversation.customer_name.ilike(f"%{name}%")
        ).group_by(
            Conversation.customer_name,
            Conversation.phone_number
        ).order_by(
            desc('last_interaction')
        )

        # Debug prints
        print(f"SQL Query: {query}")
        result = query.limit(limit).all()
        print(f"Query Result: {result}")
        
        # Additional debug
        raw_results = db.query(Conversation).filter(
            Conversation.customer_name.ilike(f"%{name}%")
        ).all()
        print(f"Raw conversations found: {len(raw_results)}")
        for conv in raw_results[:3]:  # Show first 3 results
            print(f"Customer: {conv.customer_name}, Type: {conv.customer_type}")
        
        return result

    @staticmethod
    async def get_prospect_users_by_number(
        db: Session,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get prospect users sorted by phone number with their chat statistics"""
        return db.query(
            Conversation.customer_name,
            Conversation.phone_number,
            func.count(Conversation.id).label('chat_count'),
            func.max(Conversation.created_at).label('last_interaction')
        ).filter(
            Conversation.customer_type == CustomerType.PROSPECT
        ).group_by(
            Conversation.customer_name,
            Conversation.phone_number
        ).order_by(
            desc('chat_count')
        ).limit(limit).all()
    
        
    @staticmethod
    async def get_existing_users_by_number(
        db: Session,
        phone_number: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get existing users filtered by phone number"""
        query = db.query(
            Conversation.customer_name,
            Conversation.phone_number,
            func.count(Conversation.id).label('chat_count'),
            func.max(Conversation.created_at).label('last_interaction'),
            func.string_agg(
                cast(Conversation.message, String),
                cast(' | ', String)
            ).label('recent_messages')
        ).filter(
            Conversation.customer_type.ilike('EXISTING'),  # Case-insensitive comparison
            Conversation.phone_number.ilike(f"%{phone_number}%")
        ).group_by(
            Conversation.customer_name,
            Conversation.phone_number
        ).order_by(
            desc('last_interaction')
        )

        # Debug prints
        print(f"SQL Query: {query}")
        result = query.limit(limit).all()
        print(f"Query Result: {result}")
        
        # Additional debug
        raw_results = db.query(Conversation).filter(
            Conversation.phone_number.ilike(f"%{phone_number}%")
        ).all()
        print(f"Raw conversations found: {len(raw_results)}")
        for conv in raw_results[:3]:  # Show first 3 results
            print(f"Phone: {conv.phone_number}, Type: {conv.customer_type}")
        
        return result

    @staticmethod
    async def get_conversations(
        db: Session,
        filters: ConversationFilter,
        skip: int = 0,
        limit: int = 10
    ) -> Tuple[List[Conversation], int]:
        """Get filtered conversations with pagination"""
        query = db.query(Conversation)
        
        # Apply filters
        if filters.start_date:
            query = query.filter(Conversation.created_at >= filters.start_date)
        if filters.end_date:
            query = query.filter(Conversation.created_at <= filters.end_date)
        if filters.customer_type:
            query = query.filter(Conversation.customer_type == filters.customer_type)
        if filters.sentiment:
            query = query.filter(Conversation.sentiment == filters.sentiment)
        if filters.language:
            query = query.filter(Conversation.detected_language == filters.language)
        if filters.phone_number:
            query = query.filter(Conversation.phone_number == filters.phone_number)
        if filters.customer_name:
            query = query.filter(Conversation.customer_name.ilike(f"%{filters.customer_name}%"))
        if filters.day:
            query = query.filter(func.date(Conversation.created_at) == filters.day)
        if filters.has_transfer:
            query = query.join(Transfer)
        if filters.has_bank_statement:
            query = query.join(BankStatementRequest)
        
        # Get total count for pagination
        total = query.count()
        
        # Apply pagination
        conversations = query.order_by(desc(Conversation.created_at)).offset(skip).limit(limit).all()
        
        return conversations, total 

    @staticmethod
    async def get_existing_users_by_filter(
        db: Session,
        filter: UserSearchFilter
    ) -> List[Dict[str, Any]]:
        """Get existing users filtered by name or phone number"""
        query = db.query(
            Conversation.customer_name,
            Conversation.phone_number,
            func.count(Conversation.id).label('chat_count'),
            func.max(Conversation.created_at).label('last_interaction')
        ).filter(
            Conversation.customer_type == CustomerType.CUSTOMER,
            or_(
                Conversation.customer_name.ilike(f"%{filter.search_term}%"),
                Conversation.phone_number.ilike(f"%{filter.search_term}%")
            )
        )
        
        if filter.start_date:
            query = query.filter(Conversation.created_at >= filter.start_date)
        if filter.end_date:
            query = query.filter(Conversation.created_at <= filter.end_date)
            
        return query.group_by(
            Conversation.customer_name,
            Conversation.phone_number
        ).order_by(
            desc('chat_count')
        ).limit(filter.limit).all()

    @staticmethod
    async def get_prospect_users_by_filter(
        db: Session,
        filter: UserSearchFilter
    ) -> List[Dict[str, Any]]:
        """Get prospect users filtered by phone number"""
        query = db.query(
            Conversation.customer_name,
            Conversation.phone_number,
            func.count(Conversation.id).label('chat_count'),
            func.max(Conversation.created_at).label('last_interaction')
        ).filter(
            Conversation.customer_type == CustomerType.PROSPECT,
            Conversation.phone_number.ilike(f"%{filter.search_term}%")
        )
        
        if filter.start_date:
            query = query.filter(Conversation.created_at >= filter.start_date)
        if filter.end_date:
            query = query.filter(Conversation.created_at <= filter.end_date)
            
        return query.group_by(
            Conversation.customer_name,
            Conversation.phone_number
        ).order_by(
            desc('chat_count')
        ).limit(filter.limit).all()

    @staticmethod
    async def get_user_chat_history(
        db: Session,
        filter: ChatHistoryFilter,
        customer_type: Optional[CustomerType] = None
    ) -> Tuple[List[Conversation], int]:
        """Get detailed chat history for a user"""
        query = db.query(Conversation)
        
        # Add filter conditions
        if filter.identifier:
            query = query.filter(
                or_(
                    Conversation.customer_name.ilike(f"%{filter.identifier}%"),
                    Conversation.phone_number.ilike(f"%{filter.identifier}%")
                )
            )
        
        if customer_type:
            query = query.filter(Conversation.customer_type == customer_type.value)
            
        if filter.start_date:
            query = query.filter(Conversation.created_at >= filter.start_date)
        if filter.end_date:
            query = query.filter(Conversation.created_at <= filter.end_date)

        # Debug print
        print(f"SQL Query: {query}")
        
        # Get total count for pagination
        total = query.count()
        
        # Apply sorting and pagination
        order_func = asc if filter.sort_order == "asc" else desc
        skip = (filter.page - 1) * filter.size
        
        conversations = query.order_by(
            order_func(Conversation.created_at)
        ).offset(skip).limit(filter.size).all()
        
        # Debug print
        print(f"Total Results: {total}")
        print(f"Conversations: {conversations}")
        
        return conversations, total 