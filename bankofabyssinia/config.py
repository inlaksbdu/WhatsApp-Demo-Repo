from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import os
from dotenv import load_dotenv
import logging

# Add this at the top to ensure .env is loaded
load_dotenv()

logger = logging.getLogger(__name__)

BASE_URL = os.getenv('BASE_URL')


print(f"customer endpoint in config{BASE_URL }")
#"http://18.198.5.151:9095/gticontainer/api/v1.0.0/party"

# API Configuration
BANK_API_BASE_URL = BASE_URL #"http://18.198.5.151:9095/gticontainer/api/v1.0.0/party"
CUSTOMER_INFO_ENDPOINT = f"{BANK_API_BASE_URL}/getGtCustomerInfo"
ACCOUNT_DETAILS_ENDPOINT = f"{BANK_API_BASE_URL}/getGtiAccountDetails"

# Memory Configuration
MEMORY_EXPIRY = 3600  # 1 hour in seconds

# Customer Types
class CustomerType:
    EXISTING = "EXISTING"
    PROSPECT = "PROSPECT"

# Data Models
# class CustomerDetails(BaseModel):
#     nationality: Optional[str]
#     mobileNumber: str
#     customerEmail: Optional[str]
#     fullName: Optional[str]
#     mnemonic: Optional[str]
#     industry: Optional[str]
#     dateOfBirth: Optional[str]
#     relationshipOfficer: Optional[str]
#     customerNumber: Optional[str]
#     shortName: Optional[str]
#     sector: Optional[str]
#     target: Optional[str]
    

class AccountDetails(BaseModel):
    accountNo: Optional[str]
    accountName: Optional[str]
    accountCategory: Optional[str]
    currency: Optional[str]
    openingDate: Optional[str]
    customerNo: Optional[str]
    initialDeposit: Optional[str]
    accountOfficer: Optional[str]
    customerEmail: Optional[str]
    customerTargets: Optional[str]
    target: Optional[str]
    streets: Optional[str]
    accountCreatedBy: Optional[str]

class CustomerDetails(BaseModel):
    nationality: Optional[str]
    mobileNumber: str
    customerEmail: Optional[str]
    fullName: Optional[str]
    mnemonic: Optional[str]
    industry: Optional[str]
    dateOfBirth: Optional[str]
    relationshipOfficer: Optional[str]
    customerNumber: Optional[str]
    shortName: Optional[str]
    sector: Optional[str]
    target: Optional[str]
    accounts: Optional[List[AccountDetails]] = None


class UserProfile(BaseModel):
    phone_number: str
    customer_type: str
    customer_details: Optional[CustomerDetails] = None
    last_updated: datetime

# # Response Templates
# GREETING_EXISTING = "Hello {fullName}, welcome back to GTBank! How may I assist you today?"
# GREETING_PROSPECT = """Welcome to GTBank! While I notice you don't have an account with us yet, 
# I'm happy to provide information about our services and how to open an account. How may I assist you?"""

# Error Messages
API_ERROR = "We're experiencing technical difficulties. Please try again later."
