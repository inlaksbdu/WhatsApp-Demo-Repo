from sqlalchemy.orm import Session
from sqlalchemy import func, desc, extract, and_, or_, case
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from src.models.models import Transfer, Conversation
from .schemas.request import TransferFilter, TransferStatus, TimeRangeRequest

class TransferService:
    @staticmethod
    async def get_transfer_count(
        db: Session,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get the count and statistics of transfers within a specific time range"""
        query = db.query(
            func.count(Transfer.id).label('total_transfers'),
            func.sum(Transfer.amount).label('total_amount'),
            func.avg(Transfer.amount).label('average_amount')
        ).filter(
            Transfer.date >= start_date,
            Transfer.date <= end_date
        )
        
        result = query.first()
        
        # Format time period for display
        time_period = f"{start_date.strftime('%Y-%m-%d %H:%M')} to {end_date.strftime('%Y-%m-%d %H:%M')}"
        
        return {
            "total_transfers": result.total_transfers or 0,
            "total_amount": float(result.total_amount or 0),
            "average_amount": float(result.average_amount or 0),
            "time_period": time_period
        }
    
    @staticmethod
    async def get_customers_with_most_transfers(
        db: Session,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get customers with the most transfer history"""
        # Join with Conversation to get customer details
        query = db.query(
            Conversation.customer_name,
            Conversation.phone_number,
            func.count(Transfer.id).label('total_transfers'),
            func.sum(Transfer.amount).label('total_amount'),
            func.avg(Transfer.amount).label('average_amount'),
            func.max(Transfer.date).label('last_transfer_date')
        ).join(
            Conversation, Transfer.conversation_id == Conversation.id
        ).group_by(
            Conversation.customer_name,
            Conversation.phone_number
        ).order_by(
            desc('total_transfers')
        )
        
        return query.limit(limit).all()
    
    @staticmethod
    async def get_customer_transfers_by_name(
        db: Session,
        customer_name: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 10
    ) -> Tuple[List[Transfer], int]:
        """Get transfer details for a specific customer by name within a time range"""
        query = db.query(Transfer).filter(
            Transfer.customer_name.ilike(f"%{customer_name}%")
        )
        
        if start_date:
            query = query.filter(Transfer.date >= start_date)
        if end_date:
            query = query.filter(Transfer.date <= end_date)
            
        # Get total count for pagination
        total = query.count()
        
        # Apply pagination and ordering
        transfers = query.order_by(desc(Transfer.date)).offset(skip).limit(limit).all()
        
        return transfers, total
    
    @staticmethod
    async def get_customer_transfers_by_number(
        db: Session,
        phone_number: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 10
    ) -> Tuple[List[Transfer], int]:
        """Get transfer details for a specific customer by phone number within a time range"""
        query = db.query(Transfer).join(
            Conversation, Transfer.conversation_id == Conversation.id
        ).filter(
            Conversation.phone_number == phone_number
        )
        
        if start_date:
            query = query.filter(Transfer.date >= start_date)
        if end_date:
            query = query.filter(Transfer.date <= end_date)
            
        # Get total count for pagination
        total = query.count()
        
        # Apply pagination and ordering
        transfers = query.order_by(desc(Transfer.date)).offset(skip).limit(limit).all()
        
        return transfers, total
    
    @staticmethod
    async def analyze_transfer_periods(db: Session, period_type: str = "hour") -> List[Dict[str, Any]]:
        """Analyze when transfers happen most frequently"""
        if period_type == "hour":
            # Analyze by hour of day
            query = db.query(
                extract('hour', Transfer.date).label('period'),
                func.count(Transfer.id).label('count'),
                func.sum(Transfer.amount).label('total_amount'),
                func.avg(Transfer.amount).label('average_amount')
            ).group_by('period').order_by(desc('count'))
            
            results = query.all()
            return [
                {
                    "period": f"{int(result.period):02d}:00 - {int(result.period):02d}:59",
                    "count": result.count,
                    "total_amount": float(result.total_amount or 0),
                    "average_amount": float(result.average_amount or 0)
                }
                for result in results
            ]
            
        elif period_type == "day_of_week":
            # Analyze by day of week
            query = db.query(
                extract('dow', Transfer.date).label('period'),
                func.count(Transfer.id).label('count'),
                func.sum(Transfer.amount).label('total_amount'),
                func.avg(Transfer.amount).label('average_amount')
            ).group_by('period').order_by(desc('count'))
            
            day_names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
            
            results = query.all()
            return [
                {
                    "period": day_names[int(result.period)],
                    "count": result.count,
                    "total_amount": float(result.total_amount or 0),
                    "average_amount": float(result.average_amount or 0)
                }
                for result in results
            ]
            
        elif period_type == "month":
            # Analyze by month
            query = db.query(
                extract('month', Transfer.date).label('period'),
                func.count(Transfer.id).label('count'),
                func.sum(Transfer.amount).label('total_amount'),
                func.avg(Transfer.amount).label('average_amount')
            ).group_by('period').order_by(desc('count'))
            
            month_names = ["", "January", "February", "March", "April", "May", "June", 
                          "July", "August", "September", "October", "November", "December"]
            
            results = query.all()
            return [
                {
                    "period": month_names[int(result.period)],
                    "count": result.count,
                    "total_amount": float(result.total_amount or 0),
                    "average_amount": float(result.average_amount or 0)
                }
                for result in results
            ]
        
        else:
            # Default to daily analysis
            query = db.query(
                func.date(Transfer.date).label('period'),
                func.count(Transfer.id).label('count'),
                func.sum(Transfer.amount).label('total_amount'),
                func.avg(Transfer.amount).label('average_amount')
            ).group_by('period').order_by(desc('count'))
            
            results = query.all()
            return [
                {
                    "period": result.period.strftime("%Y-%m-%d"),
                    "count": result.count,
                    "total_amount": float(result.total_amount or 0),
                    "average_amount": float(result.average_amount or 0)
                }
                for result in results
            ]
