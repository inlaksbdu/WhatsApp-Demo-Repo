from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from src.models.models import Complaint, ComplainStatus
from .schemas.request import (
    ComplaintFilter, 
    UpdateComplaintStatusRequest,
    HoldComplaintRequest,
    RejectComplaintRequest,
    ResolveComplaintRequest
)

class ComplaintService:
    @staticmethod
    async def get_complaints(
        db: Session,
        filters: Optional[ComplaintFilter] = None,
        skip: int = 0,
        limit: int = 10
    ) -> Tuple[List[Complaint], int]:
        """Get filtered complaints with pagination"""
        query = db.query(Complaint)
        
        # Apply filters if provided
        if filters:
            if filters.name:
                query = query.filter(Complaint.name.ilike(f"%{filters.name}%"))
            if filters.email:
                query = query.filter(Complaint.email == filters.email)
            if filters.phone_number:
                query = query.filter(Complaint.phone_number == filters.phone_number)
            if filters.complaint_type:
                query = query.filter(Complaint.complaint_type == filters.complaint_type)
            if filters.status:
                query = query.filter(Complaint.status == filters.status)
            if filters.start_date:
                query = query.filter(Complaint.created_at >= filters.start_date)
            if filters.end_date:
                query = query.filter(Complaint.created_at <= filters.end_date)
        
        # Get total count for pagination
        total = query.count()
        
        # Apply pagination and ordering
        complaints = query.order_by(desc(Complaint.created_at)).offset(skip).limit(limit).all()
        
        return complaints, total
    
    @staticmethod
    async def get_complaint_by_id(db: Session, complaint_id: int) -> Optional[Complaint]:
        """Get a complaint by its ID"""
        return db.query(Complaint).filter(Complaint.id == complaint_id).first()
    
    @staticmethod
    async def update_complaint_status(
        db: Session,
        complaint_id: int,
        status_update: UpdateComplaintStatusRequest
    ) -> Optional[Complaint]:
        """Update the status of a complaint"""
        complaint = await ComplaintService.get_complaint_by_id(db, complaint_id)
        
        if not complaint:
            return None
        
        complaint.status = status_update.status
        complaint.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(complaint)
        
        return complaint
    
    @staticmethod
    async def hold_complaint(
        db: Session,
        complaint_id: int,
        hold_request: HoldComplaintRequest
    ) -> Optional[Complaint]:
        """Put a complaint on hold with a reason"""
        complaint = await ComplaintService.get_complaint_by_id(db, complaint_id)
        
        if not complaint:
            return None
        
        complaint.status = ComplainStatus.ON_HOLD
        complaint.hold_reason = hold_request.hold_reason
        complaint.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(complaint)
        
        return complaint
    
    @staticmethod
    async def reject_complaint(
        db: Session,
        complaint_id: int,
        reject_request: RejectComplaintRequest
    ) -> Optional[Complaint]:
        """Reject a complaint with a reason"""
        complaint = await ComplaintService.get_complaint_by_id(db, complaint_id)
        
        if not complaint:
            return None
        
        complaint.status = ComplainStatus.REJECTED
        complaint.rejection_reason = reject_request.rejection_reason
        complaint.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(complaint)
        
        return complaint
    
    @staticmethod
    async def resolve_complaint(
        db: Session,
        complaint_id: int,
        resolve_request: ResolveComplaintRequest
    ) -> Optional[Complaint]:
        """Resolve a complaint with notes and resolver information"""
        complaint = await ComplaintService.get_complaint_by_id(db, complaint_id)
        
        if not complaint:
            return None
        
        complaint.status = ComplainStatus.COMPLETED
        complaint.resolution_notes = resolve_request.resolution_notes
        complaint.resolved_by = resolve_request.resolved_by
        complaint.resolved_at = datetime.utcnow()
        complaint.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(complaint)
        
        return complaint
