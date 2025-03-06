# import os
# import ast
# import json
# import base64
# import logging
# import asyncio
# from datetime import datetime
# from sendgrid import SendGridAPIClient
# from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition

# logger = logging.getLogger(__name__)

# class EmailService:
#     def __init__(self):
#         self.api_key = os.getenv('SENDGRID_API_KEY')
#         if not self.api_key:
#             logger.error("SENDGRID_API_KEY not found in environment variables")
#             raise ValueError("SendGrid API key not found")
        
#         self.from_email = os.getenv('SENDGRID_VERIFIED_SENDER', 'gideongyimah19@gmail.com')
#         self.sg = SendGridAPIClient(self.api_key)

#     def _parse_statement_data(self, statement_data: str) -> list:
#         """Parse the statement data from string to structured format."""
#         try:
#             # First, clean up the string by removing "Statement: "
#             clean_data = statement_data.replace("Statement: ", "")
            
#             # Use ast.literal_eval to safely evaluate the string as a Python dict
#             parsed_data = ast.literal_eval(clean_data)
            
#             # Log the parsed data for debugging
#             logger.debug(f"Parsed data: {parsed_data}")
            
#             # Extract the body list
#             transactions = parsed_data.get('body', [])
#             logger.info(f"Found {len(transactions)} transactions")
            
#             return transactions
            
#         except Exception as e:
#             logger.error(f"Failed to parse statement data: {e}")
#             logger.error(f"Raw statement data: {statement_data[:200]}...")  # Log first 200 chars
#             raise ValueError(f"Invalid statement data format: {str(e)}")
        
#     def _format_statement(self, statement_data: str, account_no: str) -> str:
#         logger.debug("Formatting statement")
#         formatted_statement = f"ACCOUNT STATEMENT\nAccount Number: {account_no}\n"
#         formatted_statement += "-" * 50 + "\n"
#         formatted_statement += "DATE          TRANSACTION          AMOUNT     BALANCE\n"
#         formatted_statement += "-" * 50 + "\n"

#         for line in statement_data.split('\n'):
#             try:
#                 if not line.strip():
#                     continue

#                 parts = line.split(':')
#                 if len(parts) >= 3:
#                     date_part = parts[0].split('*')[1].strip()
#                     transaction = parts[1].split(',')[0].strip()
#                     amount = parts[1].split('of')[-1].split(',')[0].strip()
#                     balance = parts[2].split('closing balance:')[-1].strip()
                    
#                     formatted_statement += f"{date_part:<12} {transaction:<18} {amount:<10} {balance:<10}\n"
#             except Exception as line_error:
#                 logger.warning(f"Skipping malformed line: {line_error}\nLine: {line[:50]}...")
#                 continue

#         formatted_statement += "-" * 50 + "\n"
#         formatted_statement += "\nThis statement was generated on " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#         return formatted_statement

#     async def send_statement_email(
#         self, 
#         to_email: str,
#         statement_data: str,  # Raw statement data
#         account_no: str,  # Account number added
#         subject: str = "Your Bank Statement",
#         body: str = "Please find your requested bank statement attached."
#     ) -> str:
#         try:
#             # Format the statement before creating attachment
#             formatted_statement = self._format_statement(statement_data, account_no)
            
#             message = Mail(
#                 from_email=self.from_email,
#                 to_emails=to_email,
#                 subject=subject,
#                 html_content=body
#             )
#             # Use the formatted statement for attachment
#             message.attachment = self.create_attachment(formatted_statement)
            
#             response = await asyncio.to_thread(self.sg.send, message)
#             return f"Email sent to {to_email} (Status: {response.status_code})"
#         except Exception as e:
#             error_msg = f"Email delivery failed: {str(e)}"
#             logger.error(error_msg)
#             return error_msg

#     def create_attachment(self, content: str, filename: str = "statement.pdf") -> Attachment:
#         encoded = base64.b64encode(content.encode()).decode()
#         return Attachment(
#             FileContent(encoded),
#             FileName(filename),
#             FileType("text/plain"),
#             Disposition("attachment")
#         )