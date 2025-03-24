from sqlalchemy.orm import Session
from sqlalchemy import func, desc, case, and_, or_, asc
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from src.models.models import (
    Conversation, Transfer, BankStatementRequest, 
    Complaint, Appointment, BankRequest
)
from .schemas.request import CustomerType, CustomerFilter, CustomerDetailRequest

class CustomerService:
    @staticmethod
    async def get_customer_count(db: Session) -> Dict[str, int]:
        """Get the count of customers by type"""
        total = db.query(func.count(func.distinct(Conversation.phone_number))).scalar()
        
        prospects = db.query(
            func.count(func.distinct(Conversation.phone_number))
        ).filter(
            Conversation.customer_type == CustomerType.PROSPECT
        ).scalar()
        
        existing = db.query(
            func.count(func.distinct(Conversation.phone_number))
        ).filter(
            Conversation.customer_type == CustomerType.CUSTOMER
        ).scalar()
        
        return {
            "total": total,
            "prospects": prospects,
            "existing": existing
        }
    
    @staticmethod
    async def get_most_engaged_customers(
        db: Session, 
        customer_type: Optional[CustomerType] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get customers with the most engagement (conversation count)"""
        query = db.query(
            Conversation.customer_name,
            Conversation.phone_number,
            Conversation.whatsapp_profile_name,
            Conversation.customer_type,
            func.count(Conversation.id).label('conversation_count'),
            func.max(Conversation.created_at).label('last_interaction'),
            func.avg(Conversation.polarity).label('average_sentiment_polarity')
        ).group_by(
            Conversation.customer_name,
            Conversation.phone_number,
            Conversation.whatsapp_profile_name,
            Conversation.customer_type
        )
        
        if customer_type:
            query = query.filter(Conversation.customer_type == customer_type)
        
        return query.order_by(desc('conversation_count')).limit(limit).all()
    
    @staticmethod
    async def get_customers_by_sentiment(
        db: Session,
        positive: bool = True,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get customers with the most positive or negative sentiment
        
        Args:
            db (Session): Database session
            positive (bool): If True, get most positive. If False, get most negative
            limit (int): Number of results to return
            
        Returns:
            List of customers with their sentiment statistics
        """
        # Base query to get customer sentiment statistics
        base_query = db.query(
            Conversation.customer_name,
            Conversation.phone_number,
            Conversation.whatsapp_profile_name,
            Conversation.customer_type,
            func.avg(Conversation.polarity).label('average_sentiment_polarity'),
            func.count(Conversation.id).label('conversation_count'),
            func.max(Conversation.created_at).label('last_interaction')
        ).group_by(
            Conversation.customer_name,
            Conversation.phone_number,
            Conversation.whatsapp_profile_name,
            Conversation.customer_type
        )

        # Debug print to see all sentiment values
        all_sentiments = base_query.all()
        print("\nAll customer sentiments:")
        for sentiment in all_sentiments:
            print(f"Customer: {sentiment.customer_name}, "
                  f"Avg Polarity: {sentiment.average_sentiment_polarity}, "
                  f"Conversations: {sentiment.conversation_count}")

        if positive:
            # Get customers with positive sentiment (polarity > 0)
            query = base_query.having(
                func.avg(Conversation.polarity) >= 0
            ).order_by(
                desc('average_sentiment_polarity')
            )
        else:
            # Get customers with negative sentiment (polarity < 0)
            query = base_query.having(
                func.avg(Conversation.polarity) < 0
            ).order_by(
                asc('average_sentiment_polarity')
            )

        results = query.limit(limit).all()

        # If we got results, return them
        if results:
            print(f"\nFound {len(results)} {'positive' if positive else 'negative'} sentiment results:")
            for result in results:
                print(f"Customer: {result.customer_name}, "
                      f"Avg Polarity: {result.average_sentiment_polarity}, "
                      f"Conversations: {result.conversation_count}")
            return results

        # If no results with strict filtering, try getting all results and filter in Python
        all_results = base_query.order_by(
            desc('average_sentiment_polarity') if positive else asc('average_sentiment_polarity')
        ).all()

        # Filter and sort in Python
        filtered_results = [
            r for r in all_results
            if (r.average_sentiment_polarity >= 0) == positive
        ][:limit]

        print(f"\nFound {len(filtered_results)} results after Python filtering:")
        for result in filtered_results:
            print(f"Customer: {result.customer_name}, "
                  f"Avg Polarity: {result.average_sentiment_polarity}, "
                  f"Conversations: {result.conversation_count}")

        return filtered_results
    
    @staticmethod
    async def get_customer_360_view(
        db: Session,
        request: CustomerDetailRequest
    ) -> Optional[Dict[str, Any]]:
        """Get comprehensive 360 view of a customer"""
        # Build the filter condition
        filter_conditions = []
        if request.name:
            filter_conditions.append(Conversation.customer_name == request.name)
        if request.phone_number:
            filter_conditions.append(Conversation.phone_number == request.phone_number)
        if request.customer_type:
            filter_conditions.append(Conversation.customer_type == request.customer_type)
        
        if not filter_conditions:
            return None
        
        # Get customer basic info
        customer_info = db.query(
            Conversation.customer_name,
            Conversation.phone_number,
            Conversation.whatsapp_profile_name,
            Conversation.customer_type,
            func.count(Conversation.id).label('total_conversations'),
            func.avg(Conversation.polarity).label('average_sentiment'),
            func.min(Conversation.created_at).label('first_interaction'),
            func.max(Conversation.created_at).label('last_interaction')
        ).filter(
            and_(*filter_conditions)
        ).group_by(
            Conversation.customer_name,
            Conversation.phone_number,
            Conversation.whatsapp_profile_name,
            Conversation.customer_type
        ).first()
        
        if not customer_info:
            return None
        
        # Determine channel
        channel = "WhatsApp" if customer_info.whatsapp_profile_name else "Other"
        
        # Get recent conversations
        conversations = db.query(
            Conversation.id,
            Conversation.message,
            Conversation.response,
            Conversation.sentiment,
            Conversation.polarity,
            Conversation.created_at
        ).filter(
            Conversation.phone_number == customer_info.phone_number
        ).order_by(
            desc(Conversation.created_at)
        ).limit(10).all()
        
        # Get transfers
        transfers = db.query(
            Transfer.id,
            Transfer.amount,
            Transfer.credit_account_id,
            Transfer.debit_account_id,
            Transfer.payment_details,
            Transfer.date
        ).join(
            Conversation, Transfer.conversation_id == Conversation.id
        ).filter(
            Conversation.phone_number == customer_info.phone_number
        ).order_by(
            desc(Transfer.date)
        ).limit(5).all()
        
        # Get bank statements
        bank_statements = db.query(
            BankStatementRequest.id,
            BankStatementRequest.request_start_date,
            BankStatementRequest.request_end_date,
            BankStatementRequest.date
        ).join(
            Conversation, BankStatementRequest.conversation_id == Conversation.id
        ).filter(
            Conversation.phone_number == customer_info.phone_number
        ).order_by(
            desc(BankStatementRequest.date)
        ).limit(5).all()
        
        # Get complaints
        complaints = db.query(
            Complaint.id,
            Complaint.complaint_type,
            Complaint.description,
            Complaint.status,
            Complaint.created_at
        ).join(
            Conversation, Complaint.conversation_id == Conversation.id
        ).filter(
            Conversation.phone_number == customer_info.phone_number
        ).order_by(
            desc(Complaint.created_at)
        ).limit(5).all()
        
        # Get appointments
        appointments = db.query(
            Appointment.id,
            Appointment.appointment_type,
            Appointment.preferred_date,
            Appointment.preferred_time,
            Appointment.status,
            Appointment.created_at
        ).join(
            Conversation, Appointment.conversation_id == Conversation.id
        ).filter(
            Conversation.phone_number == customer_info.phone_number
        ).order_by(
            desc(Appointment.created_at)
        ).limit(5).all()
        
        # Get bank requests
        bank_requests = db.query(
            BankRequest.id,
            BankRequest.service_type,
            BankRequest.status,
            BankRequest.created_at
        ).join(
            Conversation, BankRequest.conversation_id == Conversation.id
        ).filter(
            Conversation.phone_number == customer_info.phone_number
        ).order_by(
            desc(BankRequest.created_at)
        ).limit(5).all()
        
        return {
            "customer_name": customer_info.customer_name,
            "phone_number": customer_info.phone_number,
            "whatsapp_profile_name": customer_info.whatsapp_profile_name,
            "customer_type": customer_info.customer_type,
            "total_conversations": customer_info.total_conversations,
            "average_sentiment": customer_info.average_sentiment,
            "channel": channel,
            "first_interaction": customer_info.first_interaction,
            "last_interaction": customer_info.last_interaction,
            "conversations": conversations,
            "transfers": transfers,
            "bank_statements": bank_statements,
            "complaints": complaints,
            "appointments": appointments,
            "bank_requests": bank_requests
        }
    
    @staticmethod
    async def get_platform_channel(db: Session, phone_number: str) -> Dict[str, str]:
        """Determine the communication channel for a customer"""
        customer = db.query(
            Conversation.phone_number,
            Conversation.customer_name,
            Conversation.whatsapp_profile_name
        ).filter(
            Conversation.phone_number == phone_number
        ).first()
        
        if not customer:
            return None
        
        channel = "WhatsApp" if customer.whatsapp_profile_name else "Other"
        
        return {
            "phone_number": customer.phone_number,
            "customer_name": customer.customer_name,
            "channel": channel
        }
