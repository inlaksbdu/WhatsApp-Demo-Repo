from email.mime.application import MIMEApplication
import io
import random
import shutil
import smtplib
import ssl
import subprocess
import tempfile
from itsdangerous import TimedSerializer, BadSignature, SignatureExpired, BadData
from cryptography.fernet import Fernet
import base64
import os
from typing import Dict, Any, Optional
import orjson
from dotenv import load_dotenv
import subprocess
import boto3
from textblob import TextBlob
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from fastapi import HTTPException, Request
from pydantic import BaseModel
from datetime import date, datetime, timedelta
import time
import secrets
import json
import aiohttp
from langchain_core.messages import HumanMessage, AIMessage
import os
from sqlalchemy.orm import Session
from pydub import AudioSegment
import logging
from decouple import config
from jinja2 import Environment, FileSystemLoader
import subprocess
import boto3

from elevenlabs import ElevenLabs, VoiceSettings
import requests
import urllib.request
from textblob import TextBlob
from config import UserProfile
from googletrans import Translator
import logging
from typing import Tuple

from services.memory_service import MemoryService
from services.db_service import DatabaseService
from pathlib import Path
from io import BytesIO
from weasyprint import HTML
from PyPDF2 import PdfReader, PdfWriter
from jinja2 import Environment, FileSystemLoader
import datetime
load_dotenv()


memory_service = MemoryService()
LANGCHAIN_API_KEY = os.getenv('LANGCHAIN_API_KEY')
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_NUMBER = os.getenv('TWILIO_NUMBER')
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')

secret = os.getenv('SECRET_KEY')    

import asyncio
import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os

import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
import json
from typing import Dict, Any, Optional
from datetime import datetime
import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import sys
from loguru import logger
logger.remove(0)
logger.add(sys.stderr,level="TRACE")

from cryptography.fernet import Fernet
import base64


class PinEncryption:
    def __init__(self):
        key = secret #settings.secret_key.get_secret_value().encode()
        padded_key = base64.urlsafe_b64encode(key.ljust(32)[:32])
        self._fernet = Fernet(padded_key)

    def encrypt_pin(self, secret: str) -> str:
        return self._fernet.encrypt(secret.encode()).decode()

    def decrypt_pin(self, encrypted_str: str) -> str:
        decrypted = self._fernet.decrypt(encrypted_str.encode()).decode()
        return str(decrypted)

smtp_server = os.getenv('SMTP_SERVER')
smtp_port = int(os.getenv('SMTP_PORT', 587))
smtp_username = os.getenv('SMTP_USERNAME')
smtp_password = os.getenv('SMTP_PASSWORD')
from_email = os.getenv('FROM_EMAIL')
from pathlib import Path
# path = os.path.dirname(__file__)

def create_message(
    self,
    to_email: str,
    subject: str,
    template: str,
    attachment: dict[str, bytes] | None = None,
) -> MIMEMultipart:
    message = MIMEMultipart()
    message["Subject"] = "%s" % subject
    message["From"] = self.from_email  # Make sure this matches your class attribute name
    message["To"] = to_email
    message.attach(MIMEText(template, "html"))
    if attachment:
        for filename, file_bytes in attachment.items():
            part = MIMEApplication(file_bytes, Name=filename)
            part["Content-Disposition"] = f'attachment; filename="{filename}"'
            message.attach(part)
    return message

async def _send_email(
    self,
    to_email: str,
    message: MIMEMultipart,
) -> bool:
    try:
        context = ssl.create_default_context()
        smtp = smtplib.SMTP_SSL(
            host=self.smtp_server,
            port=self.smtp_port,
            timeout=30,  # You can adjust this timeout value
            context=context,
        )
        try:
            with smtp:
                await asyncio.to_thread(
                    smtp.login, self.from_email, self.smtp_password  # Make sure these match your class attributes
                )
                await asyncio.to_thread(smtp.send_message, message)
                self.logger.info(f"Email sent successfully to {to_email}")
                return True
        except Exception as e:
            self.logger.error(f"SMTP error sending to {to_email}: {str(e)}")
            return False
    except Exception as e:
        self.logger.error(f"Email sending failed to {to_email}: {str(e)}")
        return False
    
    
class AsyncEmailService:
    def __init__(
        self, 
        # smtp_server: Optional[str] = None,
        # smtp_port: Optional[int] = None,
        # smtp_username: Optional[str] = None,
        # smtp_password: Optional[str] = None,
        # from_email: Optional[str] = None,
    ):
        """Initialize async SMTP email service."""
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.from_email = from_email
        self.template_folder: Path = Path(__file__).parent / "services/verification/templates",
        # template_folder: Path = Path(__file__).parent / "templates",
        
        self.logger = logger
        self._validate_config()

    def _validate_config(self):
        """Validate SMTP configuration parameters."""
        missing_configs = []
        if not self.smtp_server:
            missing_configs.append("SMTP Server")
        if not self.smtp_port:
            missing_configs.append("SMTP Port")
        if not self.smtp_username:
            missing_configs.append("SMTP Username")
        if not self.smtp_password:
            missing_configs.append("SMTP Password")
        if not self.from_email:
            missing_configs.append("From Email")

        if missing_configs:
            error_msg = f"Missing SMTP configuration: {', '.join(missing_configs)}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
    def get_template(self, template_name: str, **kwargs) -> str:
        env = Environment(loader=FileSystemLoader(self.template_folder))
        template = env.get_template(template_name)
        return template.render(**kwargs)
    
    
    def _format_statement(self, transactions: Dict[str, Dict], account_no: str) -> str:
        """
        Format bank statement from transaction dictionary.
        
        Expected transaction dict format:
        {
            'transaction1': {
                'date': '2024-11-21',
                'debit': '0.00',
                'credit': '2.00',
                'balance': '2.00',
                'type': 'Transfer In'
            },
            ...
        }
        """
        # Statement header
        statement = "=" * 60 + "\n"
        statement += f"{'BANK STATEMENT':^60}\n"
        statement += "=" * 60 + "\n\n"
        statement += f"Account Number: {self._mask_account_number(account_no)}\n"
        statement += f"Statement Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        # Table header
        statement += "-" * 60 + "\n"
        statement += f"{'Date':<12}{'Type':<20}{'Debit':<10}{'Credit':<10}{'Balance':<10}\n"
        statement += "-" * 60 + "\n"

        # Transaction details
        total_credits = 0.0
        total_debits = 0.0

        for idx, (_, transaction) in enumerate(transactions.items(), 1):
            date = transaction.get('date', 'N/A')
            tx_type = transaction.get('type', 'N/A')
            debit = transaction.get('debit', '0.00')
            credit = transaction.get('credit', '0.00')
            balance = transaction.get('balance', 'N/A')

            # Accumulate totals
            # Accumulate totals
            total_credits += float(credit.replace(',', ''))
            total_debits += float(debit.replace(',', ''))

            statement += (
                f"{date:<12}"
                f"{tx_type[:20]:<20}"
                f"{debit:<10}"
                f"{credit:<10}"
                f"{balance:<10}\n"
            )

        # Footer
        statement += "-" * 60 + "\n"
        statement += f"Total Credits: ${total_credits:.2f}\n"
        statement += f"Total Debits:  ${total_debits:.2f}\n"
        statement += f"Total Transactions: {len(transactions)}\n\n"
        statement += "End of Statement\n"

        return statement

    def _mask_account_number(self, account_no: str) -> str:
        """Mask account number for privacy."""
        return f"XXXX-XXXX-{account_no[-4:]}"


    # async def send_bank_statement_email(self, __arg1: Dict[str, Any]):
    #     try:
    #         # Extract data
    #         customer_email = __arg1.get("customer_email")
    #         transactions = __arg1.get("transactions")
    #         account_no = __arg1.get("account_no")
    #         customer_name = __arg1.get("customer_name", "Valued Customer")

    #         if not all([customer_email, account_no, transactions]):
    #             raise ValueError("Missing required parameters")


    #         statement_entries = []
    #         for tx_id, tx in transactions.items():
    #             statement_entries.append({
    #                 'bookingDate': tx.get('date', 'N/A'),
    #                 'transactionNarration': tx.get('type', 'Transaction'),
    #                 'debitAccount': account_no,  # Default to account number as debit account
    #                 'creditAccount': 'Various',  # Default placeholder
    #                 'transactionRef': f"REF{tx_id[-4:]}" if tx_id[-4:].isdigit() else f"REF{tx.get('date', '')[-4:]}",
    #                 'debitAmount': tx.get('debit', '0.00'),
    #                 'creditAmount': tx.get('credit', '0.00'),
    #                 'closingBalance': tx.get('balance', '0.00')
    #             })

    #         #Create HTML content using template
    #         pdf_html = self.get_template(
    #             "statement_pdf.html",
    #             statement=statement_entries,
    #             bank_name="Akiba Commercial Bank",
    #             bank_address="Ohio Street Dar es Salaam",
    #             customer_name=customer_name,
    #             account_number=account_no,
    #             generated_date=date.today().strftime("%d %B, %Y"),
    #         )
    #         MASKED_ACCOUNT_NUMBER = account_no[:3]
    #         pin = account_no[-3:]
    #         # Convert HTML to PDF using a PDF library (e.g., WeasyPrint)
    #         pdf = HTML(string=pdf_html).write_pdf()

    #         # Create email message
    #         msg = MIMEMultipart()
    #         msg["From"] = self.smtp_username
    #         msg["To"] = customer_email
    #         msg["Subject"] = f"Bank Statement - Account {MASKED_ACCOUNT_NUMBER}XXX"

    #         # Add PDF attachment
    #         pdf_attachment = MIMEApplication(pdf, _subtype="pdf")
    #         pdf_attachment.add_header(
    #             "Content-Disposition", 
    #             "attachment", 
    #             filename=f"bank_statement_{account_no}.pdf"
    #         )
    #         msg.attach(pdf_attachment)

    #         # Send email using aiosmtplib
    #         async with aiosmtplib.SMTP(
    #             hostname=self.smtp_server,
    #             port=self.smtp_port,
    #             use_tls=False
    #         ) as smtp:
    #             await smtp.login(self.smtp_username, self.smtp_password)
    #             await smtp.send_message(msg)
    #         return {"status": "success", "message": "Bank statement sent successfully"}

    #     except aiosmtplib.SMTPException as smtp_error:
    #         error_msg = f"SMTP error: {str(smtp_error)}"
    #         self.logger.error(error_msg)
    #         raise HTTPException(status_code=500, detail=error_msg)
    #     except Exception as e:
    #         error_msg = f"Failed to send bank statement email: {str(e)}"
    #         self.logger.error(error_msg)
    #         raise HTTPException(status_code=500, detail=error_msg)
    async def send_bank_statement_email(self, __arg1: Dict[str, Any]):
        try:
            # Extract data
            customer_email = __arg1.get("customer_email")
            transactions = __arg1.get("transactions")
            account_no = __arg1.get("account_no")
            customer_name = __arg1.get("customer_name", "Valued Customer")
            


            statement_entries = []
            for tx_id, tx in transactions.items():
                statement_entries.append({
                    'bookingDate': tx.get('date', 'N/A'),
                    'transactionNarration': tx.get('type', 'Transaction'),
                    'debitAccount': account_no,
                    'creditAccount': __arg1.get("credit_account_id", "None"),
                    'transactionRef': f"REF{tx_id[-4:]}" if tx_id[-4:].isdigit() else f"REF{tx.get('date', '')[-4:]}",
                    'debitAmount': tx.get('debit', '0.00'),
                    'creditAmount': tx.get('credit', '0.00'),
                    'closingBalance': tx.get('balance', '0.00')
                })

            # Create HTML content using template
            pdf_html = self.get_template(
                "statement_pdf.html",
                statement=statement_entries,
                bank_name="Bank Of Abyssinia",
                bank_address="The Gambia st, Legehar, Addis Ababa Ethiopia",
                customer_name=customer_name,
                account_number=account_no,
                generated_date=date.today().strftime("%d %B, %Y"),
            )

            MASKED_ACCOUNT_NUMBER = account_no[:3]
            pin = account_no[-3:]  # Last 3 digits for encryption

            # Generate initial PDF
            pdf_bytes = BytesIO()
            HTML(string=pdf_html).write_pdf(pdf_bytes)
            pdf_bytes.seek(0)

            # Create encrypted PDF
            pdf_reader = PdfReader(pdf_bytes)
            pdf_writer = PdfWriter()

            # Add all pages to the writer
            for page in pdf_reader.pages:
                pdf_writer.add_page(page)

            # Encrypt with the last 3 digits
            pdf_writer.encrypt(pin, pin)

            # Get the encrypted PDF bytes
            output_pdf = BytesIO()
            pdf_writer.write(output_pdf)
            encrypted_pdf = output_pdf.getvalue()

            # Create email message
            msg = MIMEMultipart()
            msg["From"] = self.smtp_username
            msg["To"] = customer_email
            msg["Subject"] = f"Bank Statement - Account {MASKED_ACCOUNT_NUMBER}XXX"

            # Add encrypted PDF attachment
            pdf_attachment = MIMEApplication(encrypted_pdf, _subtype="pdf")
            pdf_attachment.add_header(
                "Content-Disposition", 
                "attachment", 
                filename=f"bank_statement_{MASKED_ACCOUNT_NUMBER}XXX.pdf"
            )
            msg.attach(pdf_attachment)

            # Create and attach email body with password information
            email_body = f"""
            <html>
            <body>
            <p>Dear {customer_name},</p>
            <p>Please find your bank statement attached.</p>
            <p>To open the PDF, use the last 3 digits of your account number as the password.</p>
            <p>For security reasons, if you need assistance, please contact our customer service.</p>
            <br>
            <p>Best regards,<br>Akiba Commercial Bank</p>
            </body>
            </html>
            """
            msg.attach(MIMEText(email_body, 'html'))

            # Send email using aiosmtplib
            async with aiosmtplib.SMTP(
                hostname=self.smtp_server,
                port=self.smtp_port,
                use_tls=False
            ) as smtp:
                await smtp.login(self.smtp_username, self.smtp_password)
                await smtp.send_message(msg)

            return {
                "status": "success", 
                "message": "Bank statement sent successfully",
                "details": {
                    "recipient": customer_email,
                    "account": f"{MASKED_ACCOUNT_NUMBER}XXX",
                    "password_hint": "Last 3 digits of account number"
                }
            }

        except aiosmtplib.SMTPException as smtp_error:
            error_msg = f"SMTP error: {str(smtp_error)}"
            self.logger.error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)
        except Exception as e:
            error_msg = f"Failed to send bank statement email: {str(e)}"
            self.logger.error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)        

    # async def send_bank_statement_email(
    #     self, __arg1: Dict[str, Any]
    # ) -> Dict[str, Any]:
    #     """Send bank statement via email to customer."""
    #     try:
    #         # Extract required parameters
    #         customer_email = __arg1.get("customer_email")
    #         transactions = __arg1.get("transactions")
    #         account_no = __arg1.get("account_no")

    #         # Validate required fields
    #         if not all([customer_email, transactions, account_no]):
    #             return {"status": "error", "message": "Missing required parameters"}

    #         # Validate email format
    #         if not customer_email or '@' not in customer_email:
    #             return {"status": "error", "message": f"Invalid email address: {customer_email}"}

    #         # Format statement
    #         formatted_statement = self._format_statement(transactions, account_no)

    #         # Create email message
    #         msg = MIMEMultipart()
    #         msg["From"] = self.from_email
    #         msg["To"] = customer_email
    #         msg["Subject"] = f"Account Statement - {account_no[:3]}XXXXXXXXX"

    #         # Email body
    #         body = f"""
    #         <html>
    #         <body>
    #         <strong>Your Account Statement</strong>
    #         <p>Account: {account_no[:3]}XXXXXXXXX</p>
    #         <p>Please find your requested bank statement attached.</p>
    #         </body>
    #         </html>
    #         """
    #         msg.attach(MIMEText(body, "html"))

    #         # Create attachment
    #         part = MIMEBase("application", "octet-stream")
    #         part.set_payload(formatted_statement.encode('utf-8'))
    #         encoders.encode_base64(part)
            
    #         part.add_header(
    #             "Content-Disposition", 
    #             f"attachment; filename=statement_{account_no[:3]}.txt"
    #         )
    #         msg.attach(part)

    #         # Async SMTP sending
    #         async with aiosmtplib.SMTP(
    #             hostname=self.smtp_server, 
    #             port=self.smtp_port,
    #             start_tls=True
    #         ) as server:
    #             await server.login(self.smtp_username, self.smtp_password)
    #             await server.send_message(msg)

    #         # Log successful email sending
    #         self.logger.info(f"Bank statement email sent to {customer_email}")
            
    #         return {
    #             "status": "success", 
    #             "message": "Email sent successfully",
    #             "recipient": customer_email,
    #             "account_no": account_no
    #         }
            
    #     except Exception as e:
    #         error_msg = f"Failed to send bank statement email: {str(e)}"
    #         self.logger.error(error_msg)
            
    #         return {
    #             "status": "error", 
    #             "message": error_msg,
    #             "recipient": __arg1.get("customer_email")
    #         }
        
    async def send_escalation_email(
        self, __arg1: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send a professional escalation email to bank supervisors.
        
        Args:
            __arg1 (Dict[str, Any]): Escalation email parameters
                - escalating_to (str): Email of supervisor/department
                - customer_email (str): Customer's email
                - mobile_number (str): Customer's mobile number
                - customer_name (str): Customer's full name
                - conversation_summary (str): Detailed issue description
                - customer_mood (str): Customer's emotional state
        
        Returns:
            Dict[str, Any]: Email sending status and details
        """
        try:
            # Validate and extract required parameters
            escalating_to = __arg1.get('escalating_to')
            customer_email = __arg1.get('customer_email')
            customer_name = __arg1.get('customer_name')
            conversation_summary = __arg1.get('conversation_summary')
            customer_mood = __arg1.get('customer_mood', 'Not specified')
            customer_mobile = __arg1.get('mobile_number', 'Not specified')

            # # Email validation with more robust check
            # if not all('@' in email for email in [escalating_to, customer_email]):
            #     return {
            #         "status": "error", 
            #         "message": "Invalid email address format"
            #     }

            # Construct detailed HTML email body
            email_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                <h2 style="color: #333;">Customer Service Escalation</h2>
                
                <div style="background-color: #f4f4f4; padding: 15px; border-radius: 5px;">
                    <h3>Customer Details</h3>
                    <p><strong>Name:</strong> {customer_name}</p>
                    <p><strong>Email:</strong> {customer_email}</p>
                    <p><strong>Customer Mood:</strong> {customer_mood}</p>
                    <p><strong>Mobile Number:</strong> {customer_mobile}</p>
                </div>

                <div style="margin-top: 20px;">
                    <h3>Conversation Summary</h3>
                    <p style="white-space: pre-wrap;">{conversation_summary}</p>
                </div>

                <div style="margin-top: 20px; border-top: 1px solid #ddd; padding-top: 10px; font-size: 0.9em; color: #666;">
                    <p>This is an automated escalation email. Please review and take appropriate action.</p>
                </div>
            </body>
            </html>
            """

            # Create email message
            msg = MIMEMultipart()
            msg["From"] = self.from_email
            msg["To"] = escalating_to
            msg["Subject"] = f"Urgent Customer Service Escalation - {customer_name}"

            # Attach HTML body
            msg.attach(MIMEText(email_body, "html"))

            # Async SMTP sending
            async with aiosmtplib.SMTP(
                hostname=self.smtp_server, 
                port=self.smtp_port,
                start_tls=True
            ) as server:
                await server.login(self.smtp_username, self.smtp_password)
                await server.send_message(msg)

            # Log successful escalation
            if self.logger:
                self.logger.info(
                    f"Escalation email sent to {escalating_to} "
                    f"regarding customer {customer_name}"
                )

            return {
                "status": "success", 
                "message": "Escalation email sent successfully",
                "escalated_to": escalating_to,
                "customer_name": customer_name
            }

        except Exception as e:
            # Comprehensive error logging
            error_msg = f"Escalation email failed: {str(e)}"
            if self.logger:
                self.logger.error(error_msg)
                self.logger.exception("Detailed escalation email error")

            return {
                "status": "error", 
                "message": error_msg,
                "escalated_to": __arg1.get('escalating_to')
            }
async def ogg_to_mp3_s3_local_file(audio_path: str) -> str:
    """
    Convert OGG audio to MP3, save to S3, and return the file path for Google Cloud Speech-to-Text.
    Works with local files or URLs.
    
    Args:
        audio_path: Path to local OGG file or URL of the OGG file
        
    Returns:
        str: Local file path to the MP3 file for use with Google Cloud Speech-to-Text
    """
    try:
        # Initialize S3 client
        s3_client = boto3.client('s3')
        
        # Generate unique filename using timestamp
        timestamp = int(time.time())
        filename = f"audio_transcription_{timestamp}"
        
        # File paths
        temp_ogg_path = f"/tmp/{filename}.ogg"
        temp_mp3_path = f"/tmp/{filename}.mp3"
        
        # S3 bucket and key
        s3_bucket = "whataudio"
        s3_key = f"transcriptions/{filename}.mp3"
        
        # Handle local file or URL
        if audio_path.startswith(('http://', 'https://')):
            # It's a URL - download it
            logging.info(f"Downloading from URL: {audio_path}")
            async with aiohttp.ClientSession() as session:
                async with session.get(audio_path, allow_redirects=True) as response:
                    if response.status == 200:
                        audio_data = await response.read()
                    else:
                        raise Exception(f"Failed to download audio: {response.status}")
                        
            # Save the downloaded OGG file temporarily
            with open(temp_ogg_path, 'wb') as f:
                f.write(audio_data)
        else:
            # It's a local file - copy it to temp location or use directly
            logging.info(f"Processing local file: {audio_path}")
            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"Local audio file not found: {audio_path}")
                
            # Either copy to temp location or use directly
            if os.path.dirname(audio_path) != '/tmp':
                # Copy to temp location
                shutil.copy2(audio_path, temp_ogg_path)
            else:
                # Already in temp, just use it
                temp_ogg_path = audio_path
        
        # Convert OGG to MP3 using pydub
        logging.info("Converting OGG to MP3")
        audio = AudioSegment.from_ogg(temp_ogg_path)
        audio.export(temp_mp3_path, format='mp3')
        
        # Upload to S3
        logging.info("Uploading MP3 to S3")
        with open(temp_mp3_path, 'rb') as audio_file:
            s3_client.upload_fileobj(
                audio_file, 
                s3_bucket, 
                s3_key,
                ExtraArgs={'ContentType': 'audio/mpeg'}
            )
        
        # Log S3 upload
        logging.info(f"File uploaded to S3: {s3_bucket}/{s3_key}")
        
        # Clean up the temporary OGG file if we created it
        if temp_ogg_path != audio_path and os.path.exists(temp_ogg_path):
            os.remove(temp_ogg_path)
        
        # Return the local MP3 file path for Google Cloud Speech-to-Text
        return temp_mp3_path
        
    except Exception as e:
        logging.error(f"Error in ogg_to_mp3_s3: {str(e)}")
        # Cleanup any temp files if they exist
        if 'temp_ogg_path' in locals() and os.path.exists(temp_ogg_path) and temp_ogg_path != audio_path:
            os.remove(temp_ogg_path)
        if 'temp_mp3_path' in locals() and os.path.exists(temp_mp3_path):
            os.remove(temp_mp3_path)
        raise


async def ogg_to_mp3_s3(audio_url: str) -> str:
    """
    Convert OGG audio to MP3, save to S3, and return the file path for Google Cloud Speech-to-Text
    
    Args:
        audio_url: URL of the OGG audio file
        
    Returns:
        str: Local file path to the downloaded MP3 file for use with Google Cloud Speech-to-Text
    """
    try:
        # Initialize S3 client
        s3_client = boto3.client('s3')
        
        # Generate unique filename using timestamp
        timestamp = int(time.time())
        filename = f"audio_transcription_{timestamp}"
        
        # File paths
        temp_ogg_path = f"/tmp/{filename}.ogg"
        temp_mp3_path = f"/tmp/{filename}.mp3"
        
        # S3 bucket and key
        s3_bucket = "whataudio"
        s3_key = f"transcriptions/{filename}.mp3"
        
        # Download the OGG file
        async with aiohttp.ClientSession() as session:
            async with session.get(audio_url, allow_redirects=True) as response:
                if response.status == 200:
                    audio_data = await response.read()
                else:
                    raise Exception(f"Failed to download audio: {response.status}")
        
        # Save the OGG file temporarily
        with open(temp_ogg_path, 'wb') as f:
            f.write(audio_data)
        
        # Convert OGG to MP3 using pydub
        logging.info("Converting OGG to MP3")
        audio = AudioSegment.from_ogg(temp_ogg_path)
        audio.export(temp_mp3_path, format='mp3')
        
        # Upload to S3
        logging.info("Uploading MP3 to S3")
        with open(temp_mp3_path, 'rb') as audio_file:
            s3_client.upload_fileobj(
                audio_file, 
                s3_bucket, 
                s3_key,
                ExtraArgs={'ContentType': 'audio/mpeg'}
            )
        
        # Log S3 upload
        logging.info(f"File uploaded to S3: {s3_bucket}/{s3_key}")
        
        # Clean up the temporary OGG file
        os.remove(temp_ogg_path)
        
        # Return the local MP3 file path for Google Cloud Speech-to-Text
        return temp_mp3_path
        
    except Exception as e:
        logging.error(f"Error in ogg_to_mp3_s3: {str(e)}")
        # Cleanup any temp files if they exist
        if os.path.exists(temp_ogg_path):
            os.remove(temp_ogg_path)
        if os.path.exists(temp_mp3_path):
            os.remove(temp_mp3_path)
        raise


async def text_to_whatsapp_audio(text: str) -> str:
    """
    Convert text to audio using ElevenLabs and upload to S3.
    
    Args:
        text: The text to convert to speech
        
    Returns:
        str: S3 URL of the uploaded OGG audio file
    """
    try:
        # Initialize clients
        elevenlabs_client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
        s3_client = boto3.client('s3')
        
        # Generate unique filename using timestamp
        timestamp = int(time.time())
        filename = f"response_audio_{timestamp}"
        
        # File paths (now we'll just use these temporarily)
        mp3_path = f"/tmp/{filename}.mp3"
        opus_path = f"/tmp/{filename}.ogg"
        
        # S3 bucket and key
        s3_bucket = "whataudio"
        s3_key = f"audio/{filename}.ogg"
        
        # Clean text by removing markdown formatting
        cleaned_text = text.replace("**", "").replace("*", "")
        
        logging.info("Converting text to speech with ElevenLabs")
        # Convert text to speech and handle the generator response
        audio_response = elevenlabs_client.text_to_speech.convert(
            voice_id= "UgBBYS2sOqTuMpoF3BR0", #"pNInz6obpgDQGcFmaJgB",
            output_format="mp3_22050_32",
            text=cleaned_text,
            model_id="eleven_turbo_v2_5",
            voice_settings=VoiceSettings(
                stability=0.0,
                similarity_boost=1.0,
                style=0.0,
                use_speaker_boost=True,
            ),
        )
        
        # Create a BytesIO buffer to store the audio data
        audio_buffer = io.BytesIO()
        
        # Read chunks from the generator and write to buffer
        for chunk in audio_response:
            if chunk:
                audio_buffer.write(chunk)
        
        # Save the MP3 file temporarily
        audio_buffer.seek(0)
        with open(mp3_path, 'wb') as f:
            f.write(audio_buffer.getvalue())
        
        logging.info("Converting MP3 to OGG format with Opus codec")
        # Convert MP3 to OGG using ffmpeg with opus codec
        subprocess.run([
            'ffmpeg',
            '-i', mp3_path,
            '-c:a', 'libopus',
            '-b:a', '32k',
            '-application', 'voip',  # Optimize for voice
            opus_path
        ], check=True, capture_output=True)
        
        # Upload to S3
        logging.info("Uploading audio to S3")
        with open(opus_path, 'rb') as audio_file:
            s3_client.upload_fileobj(
                audio_file, 
                s3_bucket, 
                s3_key,
                ExtraArgs={'ContentType': 'audio/ogg'}
            )
        
        # Generate a pre-signed URL (optional, but can be useful)
        s3_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': s3_bucket, 'Key': s3_key},
            ExpiresIn=3600  # URL expires in 1 hour
        )
        
        # Clean up temporary files
        os.remove(mp3_path)
        os.remove(opus_path)
        
        logging.info("Audio processing and S3 upload completed")
        return s3_url
        
    except Exception as e:
        logging.error(f"Error in text_to_whatsapp_audio: {str(e)}")
        raise

async def ogg_to_mp3_s3_url(audio_url: str) -> str:
    """
    Convert OGG audio to MP3, save to S3, and return the file path for Google Cloud Speech-to-Text
    
    Args:
        audio_url: URL of the OGG audio file
        
    Returns:
        str: Local file path to the downloaded MP3 file for use with Google Cloud Speech-to-Text
    """
    try:
        # Initialize S3 client
        s3_client = boto3.client('s3')
        
        # Generate unique filename using timestamp
        timestamp = int(time.time())
        filename = f"audio_transcription_{timestamp}"
        
        # File paths
        temp_ogg_path = f"/tmp/{filename}.ogg"
        temp_mp3_path = f"/tmp/{filename}.mp3"
        
        # S3 bucket and key
        s3_bucket = "whataudio"
        s3_key = f"transcriptions/{filename}.mp3"
        
        # Get Twilio credentials
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        
        # Download the OGG file with authentication
        async with aiohttp.ClientSession() as session:
            # Make authenticated request to Twilio media URL
            logging.info(f"Making authenticated request to Twilio media URL: {audio_url}")
            auth = aiohttp.BasicAuth(account_sid, auth_token)
            
            async with session.get(audio_url, auth=auth, allow_redirects=True) as response:
                if response.status == 200:
                    logging.info("Successfully downloaded voice message")
                    audio_data = await response.read()
                else:
                    error_msg = f"Failed to download audio: {response.status}"
                    logging.error(error_msg)
                    if response.status == 401:
                        logging.error("Authentication failed. Please check TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN")
                    raise Exception(error_msg)
        
        # Save the OGG file temporarily
        with open(temp_ogg_path, 'wb') as f:
            f.write(audio_data)
        
        # Convert OGG to MP3 using pydub
        logging.info("Converting OGG to MP3")
        audio = AudioSegment.from_ogg(temp_ogg_path)
        audio.export(temp_mp3_path, format='mp3')
        
        # Upload to S3
        logging.info("Uploading MP3 to S3")
        with open(temp_mp3_path, 'rb') as audio_file:
            s3_client.upload_fileobj(
                audio_file, 
                s3_bucket, 
                s3_key,
                ExtraArgs={'ContentType': 'audio/mpeg'}
            )
        
        # Log S3 upload
        logging.info(f"File uploaded to S3: {s3_bucket}/{s3_key}")
        
        # Clean up the temporary OGG file
        os.remove(temp_ogg_path)
        
        # Return the local MP3 file path for Google Cloud Speech-to-Text
        return temp_mp3_path
        
    except Exception as e:
        logging.error(f"Error in ogg_to_mp3_s3: {str(e)}")
        # Cleanup any temp files if they exist
        if os.path.exists(temp_ogg_path):
            os.remove(temp_ogg_path)
        if os.path.exists(temp_mp3_path):
            os.remove(temp_mp3_path)
        raise

async def generate_reference_code() -> str:
    """Generate unique reference code in format NB-YYYY-MM-DD-XXXX"""
    timestamp = datetime.now()
    random_suffix = ''.join(random.choices('0123456789', k=4))
    return f"NB-{timestamp.strftime('%Y-%m-%d')}-{random_suffix}"

from cryptography.fernet import Fernet
import base64
from urllib.parse import quote

class URLEncryption:
    def __init__(self):
        # Generate or load encryption key
        self.key = Fernet.generate_key()  # Store this securely
        self.cipher = Fernet(self.key)
    
    def encrypt_url(self, url: str) -> str:
        """Encrypt a URL"""
        encrypted_url = self.cipher.encrypt(url.encode())
        # Make the encrypted string URL-safe
        safe_url = quote(base64.urlsafe_b64encode(encrypted_url).decode())
        return safe_url
    
    def decrypt_url(self, encrypted_url: str) -> str:
        """Decrypt a URL"""
        try:
            # Convert back from URL-safe format
            encrypted_data = base64.urlsafe_b64decode(encrypted_url)
            decrypted_url = self.cipher.decrypt(encrypted_data).decode()
            return decrypted_url
        except Exception as e:
            logger.error(f"Error decrypting URL: {e}")
            raise ValueError("Invalid URL")

async def generate_secure_link(self, __arg1: Dict[str, Any]) -> Optional[Dict]:
    """Generate a secure link with encrypted backend URL"""
    try:
        customer_number = __arg1["customer_number"]
        mobile_number = __arg1["mobile_number"]
        
        # Create token
        token = self.serializer.dumps({
            'customer_number': customer_number,
            'mobile_number': mobile_number
        })
        
        # Encrypt the backend URL with token
        url_encryptor = URLEncryption()
        backend_url = "https://9ee4-2c0f-2a80-7ac-1210-dd5d-7bf2-b92b-3bfc.ngrok-free.app/verify-pin"
        encrypted_url = url_encryptor.encrypt_url(f"{backend_url}?token={token}")
        
        # Create redirect URL
        verification_link = f"https://verify.mybank.com/r/{encrypted_url}"
        
        logger.info(f"Secure link generated for customer {customer_number}")
        return verification_link
        
    except Exception as e:
        logger.error(f"Error generating secure link: {str(e)}")
        raise e
    


def get_fernet_key(hex_key: str) -> bytes:
    hex_bytes = bytes.fromhex(hex_key)
    hex_bytes = hex_bytes[:32]
    base64_key = base64.urlsafe_b64encode(hex_bytes)
    return base64_key


class SecureTokenHandler:
    def __init__(self, secret_key: str):
        self.serializer = TimedSerializer(secret_key)
        fernet_key = base64.urlsafe_b64encode(secret_key[:32].encode().ljust(32)[:32])
        self.fernet = Fernet(fernet_key)

    def generate_token(self, data: Dict[str, Any], salt: str) -> str:
        data_bytes = orjson.dumps(data)
        encrypted_data = self.fernet.encrypt(data_bytes).decode()
        token = self.serializer.dumps(encrypted_data, salt=salt)
        if isinstance(token, bytes):
            token = token.decode()
        return token

    def verify_token(self, token: str, salt: str, max_age: int) -> Optional[Dict[str, Any]]:
        try:
            encrypted_data = self.serializer.loads(token, salt=salt, max_age=max_age)
            decrypted_data = self.fernet.decrypt(encrypted_data)
            return orjson.loads(decrypted_data.decode())
            
        except (BadSignature, SignatureExpired, BadData, Exception) as e:
            print(f"Token verification failed: {str(e)}")
            return None


secure_token_handler = SecureTokenHandler(os.environ["SECRET_KEY"])



class PinVerification(BaseModel):
    pin: str

# Initialize with a secure secret key
serializer = URLSafeTimedSerializer(os.environ["SECRET_KEY"])



# async def analyze_sentiment(incoming_msg: str):
#     """
#     Analyze the sentiment of the incoming message and return polarity, subjectivity (as "subjective" or "objective"), and sentiment.
#     """
#     blob = TextBlob(incoming_msg)
#     polarity = blob.sentiment.polarity
#     subjectivity_score = blob.sentiment.subjectivity

#     # Determine sentiment based on polarity
#     if polarity > 0:
#         sentiment = "positive"
#     elif polarity < 0:
#         sentiment = "negative"
#     else:
#         sentiment = "neutral"

#     # Determine subjectivity label based on a threshold
#     if subjectivity_score >= 0.5:
#         subjectivity = "subjective"
#     else:
#         subjectivity = "objective"

#     return polarity, subjectivity, sentiment

async def analyze_multilingual_sentiment(incoming_msg: str) -> Tuple[float, str, str, str]:
    """
    Analyze the sentiment of incoming messages in multiple languages.
    Returns polarity, subjectivity (as "subjective" or "objective"), sentiment, and detected language.
    
    Args:
        incoming_msg (str): The message to analyze in any supported language
        
    Returns:
        Tuple[float, str, str, str]: (polarity, subjectivity, sentiment, detected_language)
    """
    try:
        # Create translator instance
        async with Translator() as translator:
            try:
                # Detect the language
                detection = await translator.detect(incoming_msg)
                detected_language = detection.lang
                
                # Only translate if not already in English
                if detected_language != 'en':
                    try:
                        # Translate to English
                        translation = await translator.translate(incoming_msg, dest='en')
                        translated_text = translation.text
                        blob = TextBlob(translated_text)
                    except Exception as e:
                        logging.error(f"Translation failed: {str(e)}")
                        # Fallback to original text if translation fails
                        blob = TextBlob(incoming_msg)
                else:
                    blob = TextBlob(incoming_msg)

            except Exception as e:
                logging.error(f"Language detection failed: {str(e)}")
                return 0.0, "unknown", "neutral", "unknown"

            # Get sentiment scores
            polarity = blob.sentiment.polarity
            subjectivity_score = blob.sentiment.subjectivity

            # Determine sentiment based on polarity
            if polarity > 0:
                sentiment = "positive"
            elif polarity < 0:
                sentiment = "negative"
            else:
                sentiment = "neutral"

            # Determine subjectivity label based on threshold
            if subjectivity_score >= 0.5:
                subjectivity = "subjective"
            else:
                subjectivity = "objective"

            return polarity, subjectivity, sentiment, detected_language

    except Exception as e:
        logging.error(f"Sentiment analysis failed: {str(e)}")
        return 0.0, "unknown", "neutral", "unknown"
    


def generate_secure_link(customer_number: str) -> str:
    """
    Generate a secure, obfuscated link that expires in 2 minutes
    """
    # Create payload with customer number and expiry time
    payload = {
        'customer_number': customer_number,
        'exp': (datetime.utcnow() + timedelta(minutes=2)).timestamp()
    }
    
    # Generate a random path identifier
    random_path = secrets.token_urlsafe(16)
    
    # Create encrypted token
    token = serializer.dumps(payload)
    
    # Create the verification link with random path
    verification_link = f"http://127.0.0.1:8000/v/{random_path}?t={token}"
    
    # Store the random path mapping in cache/database
    # This maps the random path to the actual endpoint temporarily
    TEMP_ROUTES[random_path] = {
        'endpoint': '/api/verify-pin',
        'expires': datetime.utcnow() + timedelta(minutes=2)
    }
    
    return verification_link


# async def process_background_tasks(
#     phone_number: str,
#     incoming_msg: str,
#     response: str,
#     profile: Any,  # Replace `Any` with the actual type of `profile`
#     whatsapp_user: str,
#     customer_name: str,
#     db: Session
# ):
#     """
#     Perform background tasks: initialize memory, log messages, analyze sentiment, and save to DB.
#     """
#     try:
#         # Initialize memory
#         await memory_service.initialize_memory(profile)

#         # Add messages to memory
#         await memory_service.add_message(phone_number, HumanMessage(content=incoming_msg))
#         await memory_service.add_message(phone_number, AIMessage(content=response))

#         # Perform sentiment analysis
#         polarity, subjectivity, sentiment = await analyze_sentiment(incoming_msg)

#         # Save conversation to the database
#         db_service = DatabaseService(db)
#         await db_service.save_conversation(
#             phone_number=phone_number,
#             customer_type=profile.customer_type,
#             message=incoming_msg,
#             response=response,
#             customer_name=customer_name,
#             whatsapp_profile_name=whatsapp_user,
#             polarity=polarity,
#             subjectivity=subjectivity,
#             sentiment=sentiment
#         )
#     except Exception as e:
#         logger.error(f"Background task error: {str(e)}")
# Store temporary route mappings
TEMP_ROUTES = {}



# async def ogg2mp3(audio_url: str) -> str:
#     """
#     Convert Twilio voice message from OGG to MP3 format with proper authentication.
    
#     Args:
#         audio_url: The Twilio media URL for the voice message
        
#     Returns:
#         str: Path to the converted MP3 file
#     """
#     logger = logging.getLogger(__name__)
    
#     # Ensure data directory exists
#     os.makedirs("data", exist_ok=True)
    
#     # Get Twilio credentials
#     account_sid = os.getenv("TWILIO_ACCOUNT_SID")
#     auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    
#     try:
#         async with aiohttp.ClientSession() as session:
#             # Make authenticated request to Twilio media URL
#             logger.info(f"Making authenticated request to Twilio media URL: {audio_url}")
#             auth = aiohttp.BasicAuth(account_sid, auth_token)
            
#             async with session.get(audio_url, auth=auth, allow_redirects=True) as response:
#                 if response.status == 200:
#                     logger.info("Successfully downloaded voice message")
#                     ogg_path = os.path.join("data", "audio.ogg")
#                     mp3_path = os.path.join("data", "audio.mp3")
                    
#                     # Save OGG file
#                     with open(ogg_path, 'wb') as f:
#                         while True:
#                             chunk = await response.content.read(8192)
#                             if not chunk:
#                                 break
#                             f.write(chunk)
#                     logger.info(f"Saved OGG file to {ogg_path}")
                    
#                     try:
#                         # Convert OGG to MP3
#                         logger.info("Converting OGG to MP3")
#                         audio = AudioSegment.from_ogg(ogg_path)
#                         audio.export(mp3_path, format="mp3")
#                         logger.info(f"Successfully converted to MP3: {mp3_path}")
                        
#                         # Clean up OGG file
#                         os.remove(ogg_path)
#                         logger.info("Cleaned up OGG file")
                        
#                         return mp3_path
                        
#                     except Exception as e:
#                         logger.error(f"Error during audio conversion: {str(e)}")
#                         # Clean up any partial files
#                         for path in [ogg_path, mp3_path]:
#                             if os.path.exists(path):
#                                 os.remove(path)
#                         raise
#                 else:
#                     error_msg = f"Failed to download voice message. Status: {response.status}"
#                     logger.error(error_msg)
#                     if response.status == 401:
#                         logger.error("Authentication failed. Please check TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN")
#                     raise Exception(error_msg)
                    
#     except aiohttp.ClientError as e:
#         logger.error(f"Network error while downloading voice message: {str(e)}")
#         raise
#     except Exception as e:
#         logger.error(f"Unexpected error in ogg2mp3: {str(e)}")
#         raise

# async def ogg2mp3(audio_url: str) -> bytes:
#     """
#     Convert Twilio voice message from OGG to MP3 format with proper authentication.
#     Returns MP3 data in memory instead of saving to disk.
    
#     Args:
#         audio_url: The Twilio media URL for the voice message
        
#     Returns:
#         bytes: MP3 audio data
#     """
#     logger = logging.getLogger(__name__)
    
#     # Get Twilio credentials
#     account_sid = os.getenv("TWILIO_ACCOUNT_SID")
#     auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    
#     try:
#         async with aiohttp.ClientSession() as session:
#             # Make authenticated request to Twilio media URL
#             logger.info(f"Making authenticated request to Twilio media URL: {audio_url}")
#             auth = aiohttp.BasicAuth(account_sid, auth_token)
            
#             async with session.get(audio_url, auth=auth, allow_redirects=True) as response:
#                 if response.status == 200:
#                     logger.info("Successfully downloaded voice message")
                    
#                     # Read OGG data into memory
#                     ogg_data = await response.content.read()
                    
#                     try:
#                         # Convert OGG to MP3 in memory
#                         audio = AudioSegment.from_ogg(io.BytesIO(ogg_data))
#                         mp3_buffer = io.BytesIO()
#                         audio.export(mp3_buffer, format="mp3")
#                         logger.info("Successfully converted to MP3")
                        
#                         return mp3_buffer.getvalue()
                        
#                     except Exception as e:
#                         logger.error(f"Error during audio conversion: {str(e)}")
#                         raise
#                 else:
#                     error_msg = f"Failed to download voice message. Status: {response.status}"
#                     logger.error(error_msg)
#                     if response.status == 401:
#                         logger.error("Authentication failed. Please check TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN")
#                     raise Exception(error_msg)
                    
#     except aiohttp.ClientError as e:
#         logger.error(f"Network error while downloading voice message: {str(e)}")
#         raise
#     except Exception as e:
#         logger.error(f"Unexpected error in ogg2mp3: {str(e)}")
#         raise
async def ogg2mp3(audio_url: str) -> bytes:
    """Convert Twilio voice message to format compatible with OpenAI Whisper"""
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    
    try:
        async with aiohttp.ClientSession() as session:
            auth = aiohttp.BasicAuth(account_sid, auth_token)
            
            async with session.get(audio_url, auth=auth, allow_redirects=True) as response:
                if response.status == 200:
                    # Read audio data into memory
                    audio_data = await response.read()
                    
                    # Create temp file for conversion
                    with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as temp_ogg:
                        temp_ogg.write(audio_data)
                        temp_ogg_path = temp_ogg.name

                    try:
                        # Convert to MP3
                        audio = AudioSegment.from_ogg(temp_ogg_path)
                        
                        # Create temp MP3 file
                        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_mp3:
                            audio.export(temp_mp3.name, format='mp3')
                            
                            # Read MP3 file into bytes
                            with open(temp_mp3.name, 'rb') as mp3_file:
                                mp3_bytes = mp3_file.read()

                        # Cleanup temp files
                        os.unlink(temp_ogg_path)
                        os.unlink(temp_mp3.name)

                        return mp3_bytes

                    except Exception as e:
                        logger.error(f"Conversion error: {str(e)}")
                        if os.path.exists(temp_ogg_path):
                            os.unlink(temp_ogg_path)
                        raise
                else:
                    raise Exception(f"Failed to download audio: {response.status}")
                    
    except Exception as e:
        logger.error(f"Audio processing error: {str(e)}")
        raise
    
    
async def process_background_tasks(
    phone_number: str,
    incoming_msg: str,
    response: str,
    profile: UserProfile,  # Changed from Any to UserProfile
    whatsapp_user: str,
    db: Session
):
    """
    Perform background tasks: initialize memory, log messages, analyze sentiment, and save to DB.
    """
    try:
        logger.info(f"Starting background tasks for {phone_number}")
        
        # Extract customer name from profile
        customer_name = profile.customer_details.fullName if profile.customer_details else "Unknown"
        logger.info(f"Customer name: {customer_name}")

        # Optional: Log all account names
        if profile.customer_details and profile.customer_details.accounts:
            account_names = [account.get('accountName') for account in profile.customer_details.accounts]
            logger.info(f"Account names: {account_names}")

        # Initialize memory
        await memory_service.initialize_memory(profile)
        logger.info(f"Memory initialized for {phone_number}")

        # Rest of the function remains the same...
        await memory_service.add_message(phone_number, HumanMessage(content=incoming_msg))
        await memory_service.add_message(phone_number, AIMessage(content=response))
        
        polarity, subjectivity, sentiment,detected_language = await analyze_multilingual_sentiment(incoming_msg)
        
        db_service = DatabaseService(db)
        await db_service.save_conversation(
            phone_number=phone_number,
            customer_type=profile.customer_type,
            message=incoming_msg,
            response=response,
            customer_name=customer_name,  # Now using the extracted name
            whatsapp_profile_name=whatsapp_user,
            polarity=polarity,
            subjectivity=subjectivity,
            detected_language = detected_language,
            sentiment=sentiment
        )
        logger.info(f"Conversation saved to DB for {phone_number}")
        
    except Exception as e:
        logger.error(f"Background task error for {phone_number}: {str(e)}")



# import io
# import random
# from itsdangerous import TimedSerializer, BadSignature, SignatureExpired, BadData
# from cryptography.fernet import Fernet
# import base64
# import os
# from typing import Dict, Any, Optional
# import orjson
# from dotenv import load_dotenv
# from textblob import TextBlob
# from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
# from fastapi import HTTPException, Request
# from pydantic import BaseModel
# from datetime import datetime, timedelta
# import secrets
# import json
# import aiohttp
# from langchain_core.messages import HumanMessage, AIMessage
# import os
# from sqlalchemy.orm import Session
# from pydub import AudioSegment
# import logging
# from decouple import config
# from jinja2 import Environment, FileSystemLoader

# import requests
# import urllib.request
# from textblob import TextBlob
# from config import UserProfile
# from googletrans import Translator
# import logging
# from typing import Tuple

# from services.memory_service import MemoryService
# from services.db_service import DatabaseService
# load_dotenv()


# memory_service = MemoryService()
# LANGCHAIN_API_KEY = os.getenv('LANGCHAIN_API_KEY')
# TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
# TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
# TWILIO_NUMBER = os.getenv('TWILIO_NUMBER')


# import asyncio
# import aiosmtplib
# from email.mime.multipart import MIMEMultipart
# from email.mime.text import MIMEText
# from email.mime.base import MIMEBase
# from email import encoders
# import os
# from typing import Dict, Any, Optional

# import asyncio
# import aiosmtplib
# from email.mime.multipart import MIMEMultipart
# from email.mime.text import MIMEText
# from email.mime.base import MIMEBase
# from email import encoders
# import os
# from typing import Dict, Any, Optional


# import os
# import logging
# import json
# from typing import Dict, Any, Optional
# from datetime import datetime


# import os
# import logging
# from typing import Dict, Any, Optional
# from datetime import datetime
# import aiosmtplib
# from email.mime.multipart import MIMEMultipart
# from email.mime.text import MIMEText
# from email.mime.base import MIMEBase
# from email import encoders
# import sys
# from loguru import logger
# logger.remove(0)
# logger.add(sys.stderr,level="TRACE")

# smtp_server = os.getenv('SMTP_SERVER')
# smtp_port = int(os.getenv('SMTP_PORT', 587))
# smtp_username = os.getenv('SMTP_USERNAME')
# smtp_password = os.getenv('SMTP_PASSWORD')
# from_email = os.getenv('FROM_EMAIL')
# from pathlib import Path
# # path = os.path.dirname(__file__)
# class AsyncEmailService:
#     def __init__(
#         self, 
#         # smtp_server: Optional[str] = None,
#         # smtp_port: Optional[int] = None,
#         # smtp_username: Optional[str] = None,
#         # smtp_password: Optional[str] = None,
#         # from_email: Optional[str] = None,
#     ):
#         """Initialize async SMTP email service."""
#         self.smtp_server = smtp_server
#         self.smtp_port = smtp_port
#         self.smtp_username = smtp_username
#         self.smtp_password = smtp_password
#         self.from_email = from_email
#         template_folder: Path = Path(__file__).parent / "templates",
#         # template_folder: Path = Path(__file__).parent / "templates",
        
#         self.logger = logger
#         self._validate_config()

#     def _validate_config(self):
#         """Validate SMTP configuration parameters."""
#         missing_configs = []
#         if not self.smtp_server:
#             missing_configs.append("SMTP Server")
#         if not self.smtp_port:
#             missing_configs.append("SMTP Port")
#         if not self.smtp_username:
#             missing_configs.append("SMTP Username")
#         if not self.smtp_password:
#             missing_configs.append("SMTP Password")
#         if not self.from_email:
#             missing_configs.append("From Email")

#         if missing_configs:
#             error_msg = f"Missing SMTP configuration: {', '.join(missing_configs)}"
#             self.logger.error(error_msg)
#             raise ValueError(error_msg)
        
#     def get_template(self, template_name: str, **kwargs) -> str:
#         env = Environment(loader=FileSystemLoader(self.template_folder))
#         template = env.get_template(template_name)
#         return template.render(**kwargs)
    
    
#     def _format_statement(self, transactions: Dict[str, Dict], account_no: str) -> str:
#         """
#         Format bank statement from transaction dictionary.
        
#         Expected transaction dict format:
#         {
#             'transaction1': {
#                 'date': '2024-11-21',
#                 'debit': '0.00',
#                 'credit': '2.00',
#                 'balance': '2.00',
#                 'type': 'Transfer In'
#             },
#             ...
#         }
#         """
#         # Statement header
#         statement = "=" * 60 + "\n"
#         statement += f"{'BANK STATEMENT':^60}\n"
#         statement += "=" * 60 + "\n\n"
#         statement += f"Account Number: {self._mask_account_number(account_no)}\n"
#         statement += f"Statement Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

#         # Table header
#         statement += "-" * 60 + "\n"
#         statement += f"{'Date':<12}{'Type':<20}{'Debit':<10}{'Credit':<10}{'Balance':<10}\n"
#         statement += "-" * 60 + "\n"

#         # Transaction details
#         total_credits = 0.0
#         total_debits = 0.0

#         for idx, (_, transaction) in enumerate(transactions.items(), 1):
#             date = transaction.get('date', 'N/A')
#             tx_type = transaction.get('type', 'N/A')
#             debit = transaction.get('debit', '0.00')
#             credit = transaction.get('credit', '0.00')
#             balance = transaction.get('balance', 'N/A')

#             # Accumulate totals
#             # Accumulate totals
#             total_credits += float(credit.replace(',', ''))
#             total_debits += float(debit.replace(',', ''))

#             statement += (
#                 f"{date:<12}"
#                 f"{tx_type[:20]:<20}"
#                 f"{debit:<10}"
#                 f"{credit:<10}"
#                 f"{balance:<10}\n"
#             )

#         # Footer
#         statement += "-" * 60 + "\n"
#         statement += f"Total Credits: ${total_credits:.2f}\n"
#         statement += f"Total Debits:  ${total_debits:.2f}\n"
#         statement += f"Total Transactions: {len(transactions)}\n\n"
#         statement += "End of Statement\n"

#         return statement

#     def _mask_account_number(self, account_no: str) -> str:
#         """Mask account number for privacy."""
#         return f"XXXX-XXXX-{account_no[-4:]}"

#     def get_template(self, template_name: str, **kwargs) -> str:
#         env = Environment(loader=FileSystemLoader(self.template_folder))
#         template = env.get_template(template_name)
#         return template.render(**kwargs)
    
#     async def send_bank_statement_email(
#         self, __arg1: Dict[str, Any]
#     ) -> Dict[str, Any]:
#         """Send bank statement via email to customer."""
#         try:
#             # Extract required parameters
#             customer_email = __arg1.get("customer_email")
#             transactions = __arg1.get("transactions")
#             account_no = __arg1.get("account_no")

#             # Validate required fields
#             if not all([customer_email, transactions, account_no]):
#                 return {"status": "error", "message": "Missing required parameters"}

#             # Validate email format
#             if not customer_email or '@' not in customer_email:
#                 return {"status": "error", "message": f"Invalid email address: {customer_email}"}

#             # Format statement
#             formatted_statement = self._format_statement(transactions, account_no)

#             # Create email message
#             msg = MIMEMultipart()
#             msg["From"] = self.from_email
#             msg["To"] = customer_email
#             msg["Subject"] = f"Account Statement - {account_no[:3]}XXXXXXXXX"

#             # Email body
#             body = f"""
#             <html>
#             <body>
#             <strong>Your Account Statement</strong>
#             <p>Account: {account_no[:3]}XXXXXXXXX</p>
#             <p>Please find your requested bank statement attached.</p>
#             </body>
#             </html>
#             """
#             msg.attach(MIMEText(body, "html"))

#             # Create attachment
#             part = MIMEBase("application", "octet-stream")
#             part.set_payload(formatted_statement.encode('utf-8'))
#             encoders.encode_base64(part)
            
#             part.add_header(
#                 "Content-Disposition", 
#                 f"attachment; filename=statement_{account_no[:3]}.txt"
#             )
#             msg.attach(part)

#             # Async SMTP sending
#             async with aiosmtplib.SMTP(
#                 hostname=self.smtp_server, 
#                 port=self.smtp_port,
#                 start_tls=True
#             ) as server:
#                 await server.login(self.smtp_username, self.smtp_password)
#                 await server.send_message(msg)

#             # Log successful email sending
#             self.logger.info(f"Bank statement email sent to {customer_email}")
            
#             return {
#                 "status": "success", 
#                 "message": "Email sent successfully",
#                 "recipient": customer_email,
#                 "account_no": account_no
#             }
            
#         except Exception as e:
#             error_msg = f"Failed to send bank statement email: {str(e)}"
#             self.logger.error(error_msg)
            
#             return {
#                 "status": "error", 
#                 "message": error_msg,
#                 "recipient": __arg1.get("customer_email")
#             }
        
#     async def send_escalation_email(
#         self, __arg1: Dict[str, Any]
#     ) -> Dict[str, Any]:
#         """
#         Send a professional escalation email to bank supervisors.
        
#         Args:
#             __arg1 (Dict[str, Any]): Escalation email parameters
#                 - escalating_to (str): Email of supervisor/department
#                 - customer_email (str): Customer's email
#                 - customer_name (str): Customer's full name
#                 - conversation_summary (str): Detailed issue description
#                 - customer_mood (str): Customer's emotional state
        
#         Returns:
#             Dict[str, Any]: Email sending status and details
#         """
#         try:
#             # Validate and extract required parameters
#             escalating_to = __arg1.get('escalating_to')
#             customer_email = __arg1.get('customer_email')
#             customer_name = __arg1.get('customer_name')
#             conversation_summary = __arg1.get('conversation_summary')
#             customer_mood = __arg1.get('customer_mood', 'Not specified')

#             # # Email validation with more robust check
#             # if not all('@' in email for email in [escalating_to, customer_email]):
#             #     return {
#             #         "status": "error", 
#             #         "message": "Invalid email address format"
#             #     }

#             # Construct detailed HTML email body
#             email_body = f"""
#             <html>
#             <body style="font-family: Arial, sans-serif; line-height: 1.6;">
#                 <h2 style="color: #333;">Customer Service Escalation</h2>
                
#                 <div style="background-color: #f4f4f4; padding: 15px; border-radius: 5px;">
#                     <h3>Customer Details</h3>
#                     <p><strong>Name:</strong> {customer_name}</p>
#                     <p><strong>Email:</strong> {customer_email}</p>
#                     <p><strong>Customer Mood:</strong> {customer_mood}</p>
#                 </div>

#                 <div style="margin-top: 20px;">
#                     <h3>Conversation Summary</h3>
#                     <p style="white-space: pre-wrap;">{conversation_summary}</p>
#                 </div>

#                 <div style="margin-top: 20px; border-top: 1px solid #ddd; padding-top: 10px; font-size: 0.9em; color: #666;">
#                     <p>This is an automated escalation email. Please review and take appropriate action.</p>
#                 </div>
#             </body>
#             </html>
#             """

#             # Create email message
#             msg = MIMEMultipart()
#             msg["From"] = self.from_email
#             msg["To"] = escalating_to
#             msg["Subject"] = f"Urgent Customer Service Escalation - {customer_name}"

#             # Attach HTML body
#             msg.attach(MIMEText(email_body, "html"))

#             # Async SMTP sending
#             async with aiosmtplib.SMTP(
#                 hostname=self.smtp_server, 
#                 port=self.smtp_port,
#                 start_tls=True
#             ) as server:
#                 await server.login(self.smtp_username, self.smtp_password)
#                 await server.send_message(msg)

#             # Log successful escalation
#             if self.logger:
#                 self.logger.info(
#                     f"Escalation email sent to {escalating_to} "
#                     f"regarding customer {customer_name}"
#                 )

#             return {
#                 "status": "success", 
#                 "message": "Escalation email sent successfully",
#                 "escalated_to": escalating_to,
#                 "customer_name": customer_name
#             }

#         except Exception as e:
#             # Comprehensive error logging
#             error_msg = f"Escalation email failed: {str(e)}"
#             if self.logger:
#                 self.logger.error(error_msg)
#                 self.logger.exception("Detailed escalation email error")

#             return {
#                 "status": "error", 
#                 "message": error_msg,
#                 "escalated_to": __arg1.get('escalating_to')
#             }



# async def generate_reference_code() -> str:
#     """Generate unique reference code in format NB-YYYY-MM-DD-XXXX"""
#     timestamp = datetime.now()
#     random_suffix = ''.join(random.choices('0123456789', k=4))
#     return f"NB-{timestamp.strftime('%Y-%m-%d')}-{random_suffix}"

# from cryptography.fernet import Fernet
# import base64
# from urllib.parse import quote

# class URLEncryption:
#     def __init__(self):
#         # Generate or load encryption key
#         self.key = Fernet.generate_key()  # Store this securely
#         self.cipher = Fernet(self.key)
    
#     def encrypt_url(self, url: str) -> str:
#         """Encrypt a URL"""
#         encrypted_url = self.cipher.encrypt(url.encode())
#         # Make the encrypted string URL-safe
#         safe_url = quote(base64.urlsafe_b64encode(encrypted_url).decode())
#         return safe_url
    
#     def decrypt_url(self, encrypted_url: str) -> str:
#         """Decrypt a URL"""
#         try:
#             # Convert back from URL-safe format
#             encrypted_data = base64.urlsafe_b64decode(encrypted_url)
#             decrypted_url = self.cipher.decrypt(encrypted_data).decode()
#             return decrypted_url
#         except Exception as e:
#             logger.error(f"Error decrypting URL: {e}")
#             raise ValueError("Invalid URL")

# async def generate_secure_link(self, __arg1: Dict[str, Any]) -> Optional[Dict]:
#     """Generate a secure link with encrypted backend URL"""
#     try:
#         customer_number = __arg1["customer_number"]
#         mobile_number = __arg1["mobile_number"]
        
#         # Create token
#         token = self.serializer.dumps({
#             'customer_number': customer_number,
#             'mobile_number': mobile_number
#         })
        
#         # Encrypt the backend URL with token
#         url_encryptor = URLEncryption()
#         backend_url = "https://9ee4-2c0f-2a80-7ac-1210-dd5d-7bf2-b92b-3bfc.ngrok-free.app/verify-pin"
#         encrypted_url = url_encryptor.encrypt_url(f"{backend_url}?token={token}")
        
#         # Create redirect URL
#         verification_link = f"https://verify.mybank.com/r/{encrypted_url}"
        
#         logger.info(f"Secure link generated for customer {customer_number}")
#         return verification_link
        
#     except Exception as e:
#         logger.error(f"Error generating secure link: {str(e)}")
#         raise e
    

# # class AsyncEmailService:
# #     def __init__(
# #         self, 
# #         smtp_server: Optional[str] = None,
# #         smtp_port: Optional[int] = None,
# #         smtp_username: Optional[str] = None,
# #         smtp_password: Optional[str] = None,
# #         from_email: Optional[str] = None,
# #         logger: Optional[Any] = None
# #     ):
# #         """
# #         Initialize async SMTP email service.
        
# #         Args:
# #             smtp_server (str, optional): SMTP server address
# #             smtp_port (int, optional): SMTP server port
# #             smtp_username (str, optional): SMTP login username
# #             smtp_password (str, optional): SMTP login password
# #             from_email (str, optional): Email address to send from
# #             logger (logging.Logger, optional): Logger instance
# #         """
# #         # Use environment variables if not provided directly
# #         self.smtp_server = smtp_server or os.getenv('SMTP_SERVER', 'smtp.gmail.com')
# #         self.smtp_port = smtp_port or int(os.getenv('SMTP_PORT', 587))
# #         self.smtp_username = smtp_username or os.getenv('SMTP_USERNAME')
# #         self.smtp_password = smtp_password or os.getenv('SMTP_PASSWORD')
# #         self.from_email = from_email or os.getenv('FROM_EMAIL')
        
# #         # Use provided logger or fallback to a default
# #         self.logger = logger

# #         # Validate required configurations
# #         self._validate_config()

# #     def _validate_config(self):
# #         """
# #         Validate SMTP configuration parameters.
# #         """
# #         missing_configs = []
# #         if not self.smtp_server:
# #             missing_configs.append("SMTP Server")
# #         if not self.smtp_port:
# #             missing_configs.append("SMTP Port")
# #         if not self.smtp_username:
# #             missing_configs.append("SMTP Username")
# #         if not self.smtp_password:
# #             missing_configs.append("SMTP Password")
# #         if not self.from_email:
# #             missing_configs.append("From Email")

# #         if missing_configs:
# #             error_msg = f"Missing SMTP configuration: {', '.join(missing_configs)}"
# #             if self.logger:
# #                 self.logger.error(error_msg)
# #             raise ValueError(error_msg)

# #     async def send_bank_statement_email(
# #         self, args: Dict[str, Any]
# #     ) -> Dict[str, Any]:
# #         """
# #         Send bank statement via email to customer.
        
# #         Args:
# #             args: Dictionary containing:
# #                     customer_email: Request Valid email address from customer, not from profile
# #                     statement_data: Raw statement data after getting account statement
# #                     account_no: Account number for reference
# #         Returns:
# #             Dict: Response from email service or error details
# #         """
# #         try:
# #             # Extract required parameters
# #             customer_email = args.get("customer_email")
# #             statement_data = args.get("statement_data")
# #             account_no = args.get("account_no")

# #             # Validate required fields
# #             if not all([customer_email, statement_data, account_no]):
# #                 return ValueError("Missing required parameters: customer_email, statement_data, or account_no")

# #             # Validate email format
# #             if not customer_email or '@' not in customer_email:
# #                 return ValueError(f"Invalid email address: {customer_email}")

# #             # Log email sending attempt
# #             if self.logger:
# #                 self.logger.info(f"Attempting to send bank statement email to {customer_email}")
# #             account_no = account_no[:3]
# #             # Create email message
# #             msg = MIMEMultipart()
# #             msg["From"] = self.from_email
# #             msg["To"] = customer_email
# #             msg["Subject"] = f"Account Statement - {account_no}XXXXXXXXX"

# #             # Create email body
# #             body = f"""
# #             <html>
# #             <body>
# #             <strong>Your Account Statement</strong>
# #             <p>Account: {account_no}XXXXXXXXX</p>
# #             <p>Please find your requested bank statement attached.</p>
# #             </body>
# #             </html>
# #             """
# #             msg.attach(MIMEText(body, "html"))

# #             # Create attachment
# #             part = MIMEBase("application", "octet-stream")
# #             part.set_payload(statement_data)
# #             encoders.encode_base64(part)
            
# #             part.add_header(
# #                 "Content-Disposition", 
# #                 f"attachment; filename=statement_{account_no}.txt"
# #             )
# #             msg.attach(part)

# #             # Async SMTP sending
# #             async with aiosmtplib.SMTP(
# #                 hostname=self.smtp_server, 
# #                 port=self.smtp_port,
# #                 start_tls=True
# #             ) as server:
# #                 # Authenticate
# #                 await server.login(self.smtp_username, self.smtp_password)
                
# #                 # Send email
# #                 await server.send_message(msg)

# #             # Log successful email sending
# #             if self.logger:
# #                 success_msg = f"Bank statement email sent successfully to {customer_email} for account {account_no}"
# #                 self.logger.info(success_msg)
            
# #             return {
# #                 "status": "success", 
# #                 "message": "Email sent successfully",
# #                 "recipient": customer_email,
# #                 "account_no": account_no
# #             }
            
# #         except Exception as e:
# #             # Log any errors
# #             if self.logger:
# #                 self.logger.error(f"Failed to send bank statement email: {str(e)}")
# #                 self.logger.exception("Email sending error details")
            
# #             return {
# #                 "status": "error", 
# #                 "message": str(e),
# #                 "recipient": args.get("customer_email")
# #             }




# # Install the async SMTP library

# def get_fernet_key(hex_key: str) -> bytes:
#     hex_bytes = bytes.fromhex(hex_key)
#     hex_bytes = hex_bytes[:32]
#     base64_key = base64.urlsafe_b64encode(hex_bytes)
#     return base64_key


# class SecureTokenHandler:
#     def __init__(self, secret_key: str):
#         self.serializer = TimedSerializer(secret_key)
#         fernet_key = base64.urlsafe_b64encode(secret_key[:32].encode().ljust(32)[:32])
#         self.fernet = Fernet(fernet_key)

#     def generate_token(self, data: Dict[str, Any], salt: str) -> str:
#         data_bytes = orjson.dumps(data)
#         encrypted_data = self.fernet.encrypt(data_bytes).decode()
#         token = self.serializer.dumps(encrypted_data, salt=salt)
#         if isinstance(token, bytes):
#             token = token.decode()
#         return token

#     def verify_token(self, token: str, salt: str, max_age: int) -> Optional[Dict[str, Any]]:
#         try:
#             encrypted_data = self.serializer.loads(token, salt=salt, max_age=max_age)
#             decrypted_data = self.fernet.decrypt(encrypted_data)
#             return orjson.loads(decrypted_data.decode())
            
#         except (BadSignature, SignatureExpired, BadData, Exception) as e:
#             print(f"Token verification failed: {str(e)}")
#             return None


# secure_token_handler = SecureTokenHandler(os.environ["SECRET_KEY"])



# class PinVerification(BaseModel):
#     pin: str

# # Initialize with a secure secret key
# serializer = URLSafeTimedSerializer(os.environ["SECRET_KEY"])



# # async def analyze_sentiment(incoming_msg: str):
# #     """
# #     Analyze the sentiment of the incoming message and return polarity, subjectivity (as "subjective" or "objective"), and sentiment.
# #     """
# #     blob = TextBlob(incoming_msg)
# #     polarity = blob.sentiment.polarity
# #     subjectivity_score = blob.sentiment.subjectivity

# #     # Determine sentiment based on polarity
# #     if polarity > 0:
# #         sentiment = "positive"
# #     elif polarity < 0:
# #         sentiment = "negative"
# #     else:
# #         sentiment = "neutral"

# #     # Determine subjectivity label based on a threshold
# #     if subjectivity_score >= 0.5:
# #         subjectivity = "subjective"
# #     else:
# #         subjectivity = "objective"

# #     return polarity, subjectivity, sentiment

# async def analyze_multilingual_sentiment(incoming_msg: str) -> Tuple[float, str, str, str]:
#     """
#     Analyze the sentiment of incoming messages in multiple languages.
#     Returns polarity, subjectivity (as "subjective" or "objective"), sentiment, and detected language.
    
#     Args:
#         incoming_msg (str): The message to analyze in any supported language
        
#     Returns:
#         Tuple[float, str, str, str]: (polarity, subjectivity, sentiment, detected_language)
#     """
#     try:
#         # Create translator instance
#         async with Translator() as translator:
#             try:
#                 # Detect the language
#                 detection = await translator.detect(incoming_msg)
#                 detected_language = detection.lang
                
#                 # Only translate if not already in English
#                 if detected_language != 'en':
#                     try:
#                         # Translate to English
#                         translation = await translator.translate(incoming_msg, dest='en')
#                         translated_text = translation.text
#                         blob = TextBlob(translated_text)
#                     except Exception as e:
#                         logging.error(f"Translation failed: {str(e)}")
#                         # Fallback to original text if translation fails
#                         blob = TextBlob(incoming_msg)
#                 else:
#                     blob = TextBlob(incoming_msg)

#             except Exception as e:
#                 logging.error(f"Language detection failed: {str(e)}")
#                 return 0.0, "unknown", "neutral", "unknown"

#             # Get sentiment scores
#             polarity = blob.sentiment.polarity
#             subjectivity_score = blob.sentiment.subjectivity

#             # Determine sentiment based on polarity
#             if polarity > 0:
#                 sentiment = "positive"
#             elif polarity < 0:
#                 sentiment = "negative"
#             else:
#                 sentiment = "neutral"

#             # Determine subjectivity label based on threshold
#             if subjectivity_score >= 0.5:
#                 subjectivity = "subjective"
#             else:
#                 subjectivity = "objective"

#             return polarity, subjectivity, sentiment, detected_language

#     except Exception as e:
#         logging.error(f"Sentiment analysis failed: {str(e)}")
#         return 0.0, "unknown", "neutral", "unknown"
    


# def generate_secure_link(customer_number: str) -> str:
#     """
#     Generate a secure, obfuscated link that expires in 2 minutes
#     """
#     # Create payload with customer number and expiry time
#     payload = {
#         'customer_number': customer_number,
#         'exp': (datetime.utcnow() + timedelta(minutes=2)).timestamp()
#     }
    
#     # Generate a random path identifier
#     random_path = secrets.token_urlsafe(16)
    
#     # Create encrypted token
#     token = serializer.dumps(payload)
    
#     # Create the verification link with random path
#     verification_link = f"http://127.0.0.1:8000/v/{random_path}?t={token}"
    
#     # Store the random path mapping in cache/database
#     # This maps the random path to the actual endpoint temporarily
#     TEMP_ROUTES[random_path] = {
#         'endpoint': '/api/verify-pin',
#         'expires': datetime.utcnow() + timedelta(minutes=2)
#     }
    
#     return verification_link


# # async def process_background_tasks(
# #     phone_number: str,
# #     incoming_msg: str,
# #     response: str,
# #     profile: Any,  # Replace `Any` with the actual type of `profile`
# #     whatsapp_user: str,
# #     customer_name: str,
# #     db: Session
# # ):
# #     """
# #     Perform background tasks: initialize memory, log messages, analyze sentiment, and save to DB.
# #     """
# #     try:
# #         # Initialize memory
# #         await memory_service.initialize_memory(profile)

# #         # Add messages to memory
# #         await memory_service.add_message(phone_number, HumanMessage(content=incoming_msg))
# #         await memory_service.add_message(phone_number, AIMessage(content=response))

# #         # Perform sentiment analysis
# #         polarity, subjectivity, sentiment = await analyze_sentiment(incoming_msg)

# #         # Save conversation to the database
# #         db_service = DatabaseService(db)
# #         await db_service.save_conversation(
# #             phone_number=phone_number,
# #             customer_type=profile.customer_type,
# #             message=incoming_msg,
# #             response=response,
# #             customer_name=customer_name,
# #             whatsapp_profile_name=whatsapp_user,
# #             polarity=polarity,
# #             subjectivity=subjectivity,
# #             sentiment=sentiment
# #         )
# #     except Exception as e:
# #         logger.error(f"Background task error: {str(e)}")
# # Store temporary route mappings
# TEMP_ROUTES = {}



# # async def ogg2mp3(audio_url: str) -> str:
# #     """
# #     Convert Twilio voice message from OGG to MP3 format with proper authentication.
    
# #     Args:
# #         audio_url: The Twilio media URL for the voice message
        
# #     Returns:
# #         str: Path to the converted MP3 file
# #     """
# #     logger = logging.getLogger(__name__)
    
# #     # Ensure data directory exists
# #     os.makedirs("data", exist_ok=True)
    
# #     # Get Twilio credentials
# #     account_sid = os.getenv("TWILIO_ACCOUNT_SID")
# #     auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    
# #     try:
# #         async with aiohttp.ClientSession() as session:
# #             # Make authenticated request to Twilio media URL
# #             logger.info(f"Making authenticated request to Twilio media URL: {audio_url}")
# #             auth = aiohttp.BasicAuth(account_sid, auth_token)
            
# #             async with session.get(audio_url, auth=auth, allow_redirects=True) as response:
# #                 if response.status == 200:
# #                     logger.info("Successfully downloaded voice message")
# #                     ogg_path = os.path.join("data", "audio.ogg")
# #                     mp3_path = os.path.join("data", "audio.mp3")
                    
# #                     # Save OGG file
# #                     with open(ogg_path, 'wb') as f:
# #                         while True:
# #                             chunk = await response.content.read(8192)
# #                             if not chunk:
# #                                 break
# #                             f.write(chunk)
# #                     logger.info(f"Saved OGG file to {ogg_path}")
                    
# #                     try:
# #                         # Convert OGG to MP3
# #                         logger.info("Converting OGG to MP3")
# #                         audio = AudioSegment.from_ogg(ogg_path)
# #                         audio.export(mp3_path, format="mp3")
# #                         logger.info(f"Successfully converted to MP3: {mp3_path}")
                        
# #                         # Clean up OGG file
# #                         os.remove(ogg_path)
# #                         logger.info("Cleaned up OGG file")
                        
# #                         return mp3_path
                        
# #                     except Exception as e:
# #                         logger.error(f"Error during audio conversion: {str(e)}")
# #                         # Clean up any partial files
# #                         for path in [ogg_path, mp3_path]:
# #                             if os.path.exists(path):
# #                                 os.remove(path)
# #                         raise
# #                 else:
# #                     error_msg = f"Failed to download voice message. Status: {response.status}"
# #                     logger.error(error_msg)
# #                     if response.status == 401:
# #                         logger.error("Authentication failed. Please check TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN")
# #                     raise Exception(error_msg)
                    
# #     except aiohttp.ClientError as e:
# #         logger.error(f"Network error while downloading voice message: {str(e)}")
# #         raise
# #     except Exception as e:
# #         logger.error(f"Unexpected error in ogg2mp3: {str(e)}")
# #         raise

# async def ogg2mp3(audio_url: str) -> bytes:
#     """
#     Convert Twilio voice message from OGG to MP3 format with proper authentication.
#     Returns MP3 data in memory instead of saving to disk.
    
#     Args:
#         audio_url: The Twilio media URL for the voice message
        
#     Returns:
#         bytes: MP3 audio data
#     """
#     logger = logging.getLogger(__name__)
    
#     # Get Twilio credentials
#     account_sid = os.getenv("TWILIO_ACCOUNT_SID")
#     auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    
#     try:
#         async with aiohttp.ClientSession() as session:
#             # Make authenticated request to Twilio media URL
#             logger.info(f"Making authenticated request to Twilio media URL: {audio_url}")
#             auth = aiohttp.BasicAuth(account_sid, auth_token)
            
#             async with session.get(audio_url, auth=auth, allow_redirects=True) as response:
#                 if response.status == 200:
#                     logger.info("Successfully downloaded voice message")
                    
#                     # Read OGG data into memory
#                     ogg_data = await response.content.read()
                    
#                     try:
#                         # Convert OGG to MP3 in memory
#                         audio = AudioSegment.from_ogg(io.BytesIO(ogg_data))
#                         mp3_buffer = io.BytesIO()
#                         audio.export(mp3_buffer, format="mp3")
#                         logger.info("Successfully converted to MP3")
                        
#                         return mp3_buffer.getvalue()
                        
#                     except Exception as e:
#                         logger.error(f"Error during audio conversion: {str(e)}")
#                         raise
#                 else:
#                     error_msg = f"Failed to download voice message. Status: {response.status}"
#                     logger.error(error_msg)
#                     if response.status == 401:
#                         logger.error("Authentication failed. Please check TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN")
#                     raise Exception(error_msg)
                    
#     except aiohttp.ClientError as e:
#         logger.error(f"Network error while downloading voice message: {str(e)}")
#         raise
#     except Exception as e:
#         logger.error(f"Unexpected error in ogg2mp3: {str(e)}")
#         raise

    
# async def process_background_tasks(
#     phone_number: str,
#     incoming_msg: str,
#     response: str,
#     profile: UserProfile,  # Changed from Any to UserProfile
#     whatsapp_user: str,
#     db: Session
# ):
#     """
#     Perform background tasks: initialize memory, log messages, analyze sentiment, and save to DB.
#     """
#     try:
#         logger.info(f"Starting background tasks for {phone_number}")
        
#         # Extract customer name from profile
#         customer_name = profile.customer_details.fullName if profile.customer_details else "Unknown"
#         logger.info(f"Customer name: {customer_name}")

#         # Optional: Log all account names
#         if profile.customer_details and profile.customer_details.accounts:
#             account_names = [account.get('accountName') for account in profile.customer_details.accounts]
#             logger.info(f"Account names: {account_names}")

#         # Initialize memory
#         await memory_service.initialize_memory(profile)
#         logger.info(f"Memory initialized for {phone_number}")

#         # Rest of the function remains the same...
#         await memory_service.add_message(phone_number, HumanMessage(content=incoming_msg))
#         await memory_service.add_message(phone_number, AIMessage(content=response))
        
#         polarity, subjectivity, sentiment,detected_language = await analyze_multilingual_sentiment(incoming_msg)
        
#         db_service = DatabaseService(db)
#         await db_service.save_conversation(
#             phone_number=phone_number,
#             customer_type=profile.customer_type,
#             message=incoming_msg,
#             response=response,
#             customer_name=customer_name,  # Now using the extracted name
#             whatsapp_profile_name=whatsapp_user,
#             polarity=polarity,
#             subjectivity=subjectivity,
#             detected_language = detected_language,
#             sentiment=sentiment
#         )
#         logger.info(f"Conversation saved to DB for {phone_number}")
        
#     except Exception as e:
#         logger.error(f"Background task error for {phone_number}: {str(e)}")