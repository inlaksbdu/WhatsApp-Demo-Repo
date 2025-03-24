import enum
from dotenv import load_dotenv
import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, ForeignKey, Enum, JSON, Boolean
from sqlalchemy.engine import URL
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship
from datetime import datetime
from sqlalchemy import text
import os
from dotenv import load_dotenv
# url = URL.create(
#     drivername="postgresql",
#     username='inlaks_wa_db',
#     password='IF2wgCky30NtKp2JuIAr',
#     host="inlaks-wa-db.cnuese2serq4.eu-central-1.rds.amazonaws.com",
#     database="postgres",
#     port=5432,
# )


# Load environment variables from .env file
load_dotenv()

# Access the environment variables
db_username = os.getenv('DB_USERNAME')
db_host = os.getenv('DB_HOST')
db = os.getenv('DB_NAME')
db_password = os.getenv('DB_PASSWORD')
db_port = os.getenv('DB_PORT')
db_drivername = os.getenv('DB_DRIVERNAME')
db_port = int(db_port)


url = URL.create(
    drivername=db_drivername,
    username=db_username,
    password= db_password,
    host=db_host,
    database=db,
    port=db_port,
)
# postgresql://neondb_owner:GOjQxz9In0DF@ep-snowy-leaf-a56ztp79-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require
engine = create_engine(
    url,
    connect_args={
        "sslmode": "require"
    }
)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class AppointmentStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    RESCHEDULED = "rescheduled"

class CancellationReason(str, enum.Enum):
    CUSTOMER_REQUEST = "customer_request"
    SCHEDULE_CONFLICT = "schedule_conflict"
    EMERGENCY = "emergency"
    NO_SHOW = "no_show"
    RESCHEDULED = "rescheduled"
    OTHER = "other"
class AppointmentType(str, enum.Enum):
    ACCOUNT_OPENING = "account_opening"
    LOAN_CONSULTATION = "loan_consultation"
    INVESTMENT_ADVISORY = "investment_advisory"
    GENERAL_INQUIRY = "general_inquiry"
    COMPLAINT_RESOLUTION = "complaint_resolution"
    OTHER = "other"

class RejectionReason(str, enum.Enum):
    INCOMPLETE_DOCUMENTS = "incomplete_documents"
    INVALID_REQUEST = "invalid_request"
    SERVICE_UNAVAILABLE = "service_unavailable"
    OUTSIDE_SERVICE_AREA = "outside_service_area"
    STAFF_UNAVAILABLE = "staff_unavailable"
    OTHER = "other"

class ComplainStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "resolved"
    ON_HOLD = "on_hold"
    REJECTED = "rejected"

class RequestStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    ON_HOLD = "on_hold"
    REJECTED = "rejected"


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, index=True)
    customer_name = Column(String)
    whatsapp_profile_name = Column(String) 
    customer_type = Column(String)  # CUSTOMER or PROSPECT
    message = Column(Text)
    response = Column(Text)
    sentiment = Column(String)  # POSITIVE, NEGATIVE, NEUTRAL
    polarity = Column(Float)
    subjectivity = Column(Text)
    detected_language = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Add relationships
    transfers = relationship("Transfer", back_populates="conversation")
    bank_statement_requests = relationship("BankStatementRequest", back_populates="conversation")
    complaints = relationship("Complaint", back_populates="conversation")
    appointments = relationship("Appointment", back_populates="conversation")
    bank_requests = relationship("BankRequest", back_populates="conversation")


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String, index=True)
    email = Column(String)
    phone_number = Column(String, index=True)
    appointment_type = Column(Enum(AppointmentType))
    preferred_date = Column(DateTime)
    preferred_time = Column(String)  # Store time as HH:MM format
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.PENDING)
    reference_code = Column(String, unique=True, index=True) 
    
    # Reason tracking
    cancellation_reason = Column(Enum(CancellationReason), nullable=True)
    rejection_reason = Column(Enum(RejectionReason), nullable=True)
    reason_details = Column(Text, nullable=True)  # Additional explanation
    suggested_alternative_date = Column(DateTime, nullable=True)
    suggested_alternative_time = Column(String, nullable=True)
    
    location = Column(String)  # Physical location or 'virtual'
    additional_notes = Column(Text, nullable=True)
    assigned_agent = Column(String, nullable=True)
    
    # If this appointment was created through a conversation
    conversation_id = Column(Integer, ForeignKey('conversations.id', ondelete='SET NULL'), nullable=True)
    conversation = relationship("Conversation", back_populates="appointments")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    cancelled_at = Column(DateTime, nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    action_by = Column(String, nullable=True)  
    last_reminder_sent = Column(DateTime, nullable=True)
    confirmation_sent = Column(Boolean, default=False)
    feedback_rating = Column(Integer, nullable=True)
    feedback_comments = Column(Text, nullable=True)
    attendance_status = Column(String, nullable=True)  # 'attended', 'no_show', etc.


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, index=True)
    phone_number = Column(String, index=True)
    complaint_type = Column(String)
    description = Column(Text)
    status = Column(Enum(ComplainStatus), default=ComplainStatus.PENDING) # PENDING, IN_PROGRESS, RESOLVED, CLOSED
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    conversation_id = Column(Integer, ForeignKey('conversations.id', ondelete='SET NULL'), nullable=True)
    conversation = relationship("Conversation", back_populates="complaints")
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    rejection_reason = Column(String, nullable=True)
    hold_reason = Column(String, nullable=True)

class PinManagement(Base):
    __tablename__ = "pin_management"

    id = Column(Integer, primary_key=True, index=True)
    customer_number = Column(String, unique=True, index=True, nullable=False)
    encrypted_pin = Column(Text, nullable=False)


class BankRequest(Base):
    __tablename__ = "bank_requests"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String)
    customer_name = Column(String)
    reference_code = Column(String, unique=True, index=True)  # NB-YYYY-MM-DD-XXXX 
    service_type = Column(String)  # Account/Loan/Card/Transfer/Investment
    service_details = Column(JSON)  # Store service-specific details as JSON
    status = Column(Enum(RequestStatus), default=RequestStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    processed_by = Column(String, nullable=True)
    processing_notes = Column(Text, nullable=True)
    rejection_reason = Column(String, nullable=True)
    expiry_date = Column(DateTime, nullable=True)
    last_status_update = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    conversation_id = Column(Integer, ForeignKey('conversations.id', ondelete='SET NULL'), nullable=True)
    conversation = relationship("Conversation", back_populates="bank_requests")

class Transfer(Base):
    __tablename__ = "transfers"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String, index=True)
    amount = Column(Float)
    credit_account_id = Column(String)
    debit_account_id = Column(String)
    payment_details = Column(Text)
    date = Column(DateTime, default=datetime.utcnow)
    conversation_id = Column(Integer, ForeignKey('conversations.id', ondelete='SET NULL'), nullable=True)
    
    # Add relationship to Conversation
    conversation = relationship("Conversation", back_populates="transfers")

class BankStatementRequest(Base):
    __tablename__ = "bank_statement_requests"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String, index=True)
    request_start_date = Column(DateTime)
    request_end_date = Column(DateTime)
    date = Column(DateTime, default=datetime.utcnow)
    conversation_id = Column(Integer, ForeignKey('conversations.id', ondelete='SET NULL'), nullable=True)
    
    # Add relationship to Conversation
    conversation = relationship("Conversation", back_populates="bank_statement_requests")

class OTPManagement(Base):
    __tablename__ = "otp_management"

    id = Column(Integer, primary_key=True, index=True)
    identifier = Column(String, unique=True, index=True, nullable=False)
    otp_code = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)

# # # Add this before Base.metadata.create_all(engine)
# with engine.connect() as conn:
#     conn.execute(text("DROP TABLE IF EXISTS cappointments;"))
#     conn.commit()

Base.metadata.create_all(engine)

from sqlalchemy import inspect

def check_if_column_exists():
    inspector = inspect(engine)
    columns = [c['name'] for c in inspector.get_columns('conversations')]
    print("Existing columns:", columns)

def check_if_column_exists1():
    inspector = inspect(engine)
    columns = [c['name'] for c in inspector.get_columns('bank_requests')]
    print("Existing columns for requests:", columns)
# Add this after your engine creation to see what columns exist
check_if_column_exists()
check_if_column_exists1()
# # Warning: This deletes existing data!


# with engine.connect() as conn:
#     conn.execute(text("ALTER TABLE conversations ADD COLUMN whatsapp_profile_name VARCHAR;"))
#     conn.commit()



# Dependency
def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


