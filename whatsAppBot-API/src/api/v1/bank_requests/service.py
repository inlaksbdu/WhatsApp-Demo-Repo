from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from src.models.models import BankRequest, RequestStatus
from .schemas.request import (
    BankRequestFilter, 
    UpdateRequestStatusRequest,
    RejectRequestRequest,
    ResolveRequestRequest
)

class BankRequestService:
    @staticmethod
    async def get_bank_requests(
        db: Session,
        filters: Optional[BankRequestFilter] = None,
        skip: int = 0,
        limit: int = 10
    ) -> Tuple[List[BankRequest], int]:
        """Get filtered bank requests with pagination"""
        query = db.query(BankRequest)
        
        # Apply filters if provided
        if filters:
            if filters.email:
                query = query.filter(BankRequest.email == filters.email)
            if filters.customer_name:
                query = query.filter(BankRequest.customer_name.ilike(f"%{filters.customer_name}%"))
            if filters.reference_code:
                query = query.filter(BankRequest.reference_code == filters.reference_code)
            if filters.service_type:
                query = query.filter(BankRequest.service_type == filters.service_type)
            if filters.status:
                query = query.filter(BankRequest.status == filters.status)
            if filters.start_date:
                query = query.filter(BankRequest.created_at >= filters.start_date)
            if filters.end_date:
                query = query.filter(BankRequest.created_at <= filters.end_date)
        
        # Get total count for pagination
        total = query.count()
        
        # Apply pagination and ordering
        requests = query.order_by(desc(BankRequest.created_at)).offset(skip).limit(limit).all()
        
        return requests, total
    
    @staticmethod
    async def get_bank_request_by_id(db: Session, request_id: int) -> Optional[BankRequest]:
        """Get a bank request by its ID"""
        return db.query(BankRequest).filter(BankRequest.id == request_id).first()
    
    @staticmethod
    async def update_request_status(
        db: Session,
        request_id: int,
        status_update: UpdateRequestStatusRequest
    ) -> Optional[BankRequest]:
        """Update the status of a bank request"""
        bank_request = await BankRequestService.get_bank_request_by_id(db, request_id)
        
        if not bank_request:
            return None
        
        bank_request.status = status_update.status
        bank_request.last_status_update = datetime.utcnow()
        
        db.commit()
        db.refresh(bank_request)
        
        return bank_request
    
    @staticmethod
    async def reject_request(
        db: Session,
        request_id: int,
        reject_request: RejectRequestRequest
    ) -> Optional[BankRequest]:
        """Reject a bank request with a reason"""
        bank_request = await BankRequestService.get_bank_request_by_id(db, request_id)
        
        if not bank_request:
            return None
        
        bank_request.status = RequestStatus.REJECTED
        bank_request.rejection_reason = reject_request.rejection_reason
        bank_request.last_status_update = datetime.utcnow()
        
        db.commit()
        db.refresh(bank_request)
        
        return bank_request
    
    @staticmethod
    async def resolve_request(
        db: Session,
        request_id: int,
        resolve_request: ResolveRequestRequest
    ) -> Optional[BankRequest]:
        """Resolve a bank request with notes and processor information"""
        bank_request = await BankRequestService.get_bank_request_by_id(db, request_id)
        
        if not bank_request:
            return None
        
        bank_request.status = RequestStatus.COMPLETED
        bank_request.processing_notes = resolve_request.processing_notes
        bank_request.processed_by = resolve_request.processed_by
        bank_request.processed_at = datetime.utcnow()
        bank_request.last_status_update = datetime.utcnow()
        
        db.commit()
        db.refresh(bank_request)
        
        return bank_request
