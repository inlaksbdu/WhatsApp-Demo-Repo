import base64
import io
from math import pi
import os
import logging
from typing import Optional, Dict, Any, List, Annotated, TypedDict, Literal
from fastapi import FastAPI,BackgroundTasks, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from pydantic import BaseModel, ConfigDict
from twilio.rest import Client
from typing import Literal
from langchain.output_parsers.openai_tools import JsonOutputToolsParser
from langchain_core.messages import ToolMessage
from datetime import datetime
import uvicorn
from tenacity import retry, stop_after_attempt, wait_exponential
import traceback
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import aiohttp
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.tools import Tool
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langgraph.store.memory import InMemoryStore
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader
from langchain.tools.retriever import create_retriever_tool
from langchain_community.tools.tavily_search import TavilySearchResults
from prompt import get_system_prompt
from services.profile_service import ProfileService
from services.memory_service import MemoryService
from config import UserProfile
# from langchain_huggingface import HuggingFaceEmbeddings
from config import CustomerType
from models.database import PinManagement, get_db, Conversation
from services.db_service import DatabaseService
from tools.tools import BankingTools
from enum import Enum
# from loguru import logger
from utils import TEMP_ROUTES, get_fernet_key, ogg2mp3, ogg_to_mp3_s3, ogg_to_mp3_s3_url, process_background_tasks
from cryptography.fernet import Fernet
from analytics_routes import users_analytics #, modelling_routes
import assemblyai as aai
from config import CUSTOMER_INFO_ENDPOINT
from langchain_openai import OpenAIEmbeddings
import pytz
from langchain_core.vectorstores import InMemoryVectorStore
from openai import OpenAI
from langchain_google_community import SpeechToTextLoader
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg import Connection
from psycopg_pool import ConnectionPool
import nest_asyncio
# nest_asyncio.apply()
from loguru import logger
os.environ["TOKENIZERS_PARALLELISM"] = "false"
assemply_key = os.getenv('ASSEMBLY_AI_API_KEY ')
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     handlers=[
#         logging.StreamHandler(),  # Log to console
#         logging.FileHandler('app.log')  # Log to file
#     ]
# )
# logger = logging.getLogger(__name__)

# Load environment variables


# Connection configuration

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')
HF_TOKEN = os.getenv('HF_TOKEN')
LANGCHAIN_API_KEY = os.getenv('LANGCHAIN_API_KEY')
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_NUMBER = os.getenv('TWILIO_NUMBER')
BACKEND_URL = os.getenv('BACKEND_URL')
VERIFY_URL = os.getenv('VERIFY_URL')
PROJECT_ID = os.getenv('PROJECT_ID')
db_username = os.getenv('DB_USERNAME')
db_host = os.getenv('DB_HOST')
db = os.getenv('DB_NAME')
db_password = os.getenv('DB_PASSWORD')
db_port = os.getenv('DB_PORT')
db_drivername = os.getenv('DB_DRIVERNAME')
db_port = int(db_port)
os.environ['LANGCHAIN_API_KEY'] = LANGCHAIN_API_KEY
os.environ['LANGCHAIN_TRACING_V2'] = 'true'
os.environ['LANGCHAIN_PROJECT'] = 'Inlaks'
os.environ['TAVILY_API_KEY'] = TAVILY_API_KEY
os.environ['HF_TOKEN'] = HF_TOKEN
serializer = URLSafeTimedSerializer(os.environ["SECRET_KEY"])
import httpx

client = OpenAI()
fernet = Fernet(get_fernet_key(os.environ["SECRET_KEY"]))

template = Jinja2Templates(directory="template")

class AccountCreationLog(BaseModel):
    success: bool
    status: int
    response: Dict[str, Any]
    request_data: Dict[str, Any]

templates = Jinja2Templates(directory="templates")


class PinVerification(BaseModel):
    secure_pin: str

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


app = FastAPI(title="CBG WhatsApp Bot")

profile_service = ProfileService()
memory_service = MemoryService()

in_memory_store = InMemoryStore()  
within_thread_memory = MemorySaver()

tools = []




async def send_whatsapp_message(to_number: str, body_text: str):
    """Send WhatsApp message using Twilio client"""
    try:
        message = twilio_client.messages.create(
            from_=f"whatsapp:{TWILIO_NUMBER}",
            body=body_text,
            to=f"whatsapp:{to_number}"
        )
        logger.info(f"Message sent successfully to {to_number}")
        return message
    except Exception as e:
        logger.error(f"Error sending message to {to_number}: {e}")
        raise

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# app.model_config = ConfigDict(arbitrary_types_allowed=True)
# app.include_router(users_analytics.router)
# app.include_router(modelling_routes.router)

# BANK_URLS = [
#     "https://www.cbg.com.gh/",
#     "https://www.cbg.com.gh/about-cbg.html",
#     "https://www.cbg.com.gh/board-of-directors.html",
#     "https://www.cbg.com.gh/executive-management.html",
#     "https://www.cbg.com.gh/persa-loans-profile.html",
#     "https://www.cbg.com.gh/classic-current-account.html",
#     "https://www.cbg.com.gh/contact-us.html",
#     "https://www.cbg.com.gh/services.html",
#     "https://ibank.cbg.com.gh/EPS_INT_CORP/",
#     "https://www.cbg.com.gh/sustainability-commitment-statement.html",
#     "https://cbg.com.gh/news/",
#     "https://www.cbg.com.gh/digital.html",
#     "https://www.cbg.com.gh/cbg-atms---branches.html",
#     "https://cbg.com.gh/rates.html"
# ]

# BANK_URLS = [
# 'https://www.acbbank.co.tz/',
# 'https://www.acbbank.co.tz/about-us/background/',
# 'https://www.acbbank.co.tz/about-us/mission-vision/',
# 'https://www.acbbank.co.tz/about-us/board-members/'
# 'https://www.acbbank.co.tz/about-us/senior-management/',
# 'https://www.acbbank.co.tz/savings-accounts/',
# 'https://www.acbbank.co.tz/deposits/current-account/',
# 'https://www.acbbank.co.tz/deposits/time-deposits/',
# 'https://www.acbbank.co.tz/savings-accounts/waridi-account/',
# 'https://www.acbbank.co.tz/loans/biashara-loans/',
# 'https://www.acbbank.co.tz/loans/micro-loan/',
# 'https://www.acbbank.co.tz/loans/home-improvement-loan/',
# 'https://www.acbbank.co.tz/loans/salaried-loans/',
# 'https://www.acbbank.co.tz/loans/overdraft-facility/',
# 'https://www.acbbank.co.tz/insurance/insurance-premium-finance-ipf/',
# 'https://www.acbbank.co.tz/insurance/motor-vehicle-insurance/',
# 'https://www.acbbank.co.tz/insurance/fire-insurance-allied-perils/',
# 'https://www.acbbank.co.tz/insurance/goods-in-transit/',
# 'https://www.acbbank.co.tz/insurance/life-insurance/',
# 'https://www.acbbank.co.tz/domestic-package-insurance/',
# 'https://www.acbbank.co.tz/fire-business/',
# 'https://www.acbbank.co.tz/burglary-insurance/',
# 'https://www.acbbank.co.tz/akiba-wakala/',
# 'https://www.acbbank.co.tz/akiba-mobile/',
# 'https://www.acbbank.co.tz/atm-services/',
# 'https://www.acbbank.co.tz/super-agent/',
# 'https://www.acbbank.co.tz/visa/',
# 'https://www.acbbank.co.tz/digital-financial-services/',
# 'https://www.acbbank.co.tz/akiba-money-tansfer/tiss/',
# 'https://www.acbbank.co.tz/investors/',
# 'https://www.acbbank.co.tz/quarterly-reports/',
# 'https://www.acbbank.co.tz/atm-branches/',
# 'https://www.acbbank.co.tz/contact-us/'
# ]
BANK_URLS =[
    'https://www.bankofabyssinia.com/',
    'https://www.bankofabyssinia.com/about-bank-of-abyssinia-first-bank/',
    'https://apollo.bankofabyssinia.com/',
    'https://www.bankofabyssinia.com/saving-account/',
    'https://www.bankofabyssinia.com/current-account/',
    'https://www.bankofabyssinia.com/fixed-time-account/',
    'https://www.bankofabyssinia.com/more-services/',
    'https://www.bankofabyssinia.com/exchange-rate-2/',
    'https://www.bankofabyssinia.com/foreign-currency-deposit-accounts/',
    'https://www.bankofabyssinia.com/trade-services/',
    'https://www.bankofabyssinia.com/correspondent-banks/',
    'https://www.bankofabyssinia.com/money-transfer/',
    'https://www.bankofabyssinia.com/corporate-and-commercial-credit-products/',
    'https://www.bankofabyssinia.com/consumer-and-mortgage-products/',
    'https://www.bankofabyssinia.com/bank-guarantee/',
    'https://www.bankofabyssinia.com/loan-calculator/',
    'https://www.bankofabyssinia.com/abyssinia-online-corporate-online-banking/',
    'https://www.bankofabyssinia.com/agent-banking/',
    'https://www.bankofabyssinia.com/card-banking/',
    'https://www.bankofabyssinia.com/mobile-banking-in-ethiopia/',
    'https://www.bankofabyssinia.com/virtual-banking-in-ethiopia/',
    'https://www.bankofabyssinia.com/branch-atm-locations/',
    'https://www.bankofabyssinia.com/tariffs/',
    'https://donate.bankofabyssinia.com/dashboard/',
    'https://www.bankofabyssinia.com/abyssinia-ecommerce-payment-visa/',
    'https://www.bankofabyssinia.com/ifb-deposit-accounts-2/',
    'https://www.bankofabyssinia.com/fcy-deposit-account/',
    'https://www.bankofabyssinia.com/ifb-financing-products/',
    'https://www.bankofabyssinia.com/news/',
    'https://www.bankofabyssinia.com/blog/',
    'https://www.bankofabyssinia.com/annual-reports/'

]
# BANK_URLS = [
# 'https://www.novabank.ng/',
# 'https://www.novabank.ng/our-history/',
# 'https://www.novabank.ng/who-we-are/',
# 'https://www.novabank.ng/leadership/',
# 'https://novabank.ng/financials/',
# 'https://novabank.ng/service/personal-banking/',
# 'https://novabank.ng/service/business-banking/',
# 'https://novabank.ng/service/corporate-banking/',
# 'https://novabank.ng/service/investment-banking/',
# 'https://novabank.ng/service/treasury/',
# 'https://novabank.ng/service/trade-services/',
# 'https://novabank.ng/service/nova-uplift-initiative/',
# 'https://novabank.ng/service/investor-relations/',
# 'https://novabank.ng/newsroom/',
# 'https://novabank.ng/press-releases/',
# 'https://novabank.ng/press-releases/annual-reports/',
# 'https://novabank.ng/image-gallery/',
# 'https://novabank.ng/research-archive/',
# 'https://novabank.ng/downloads/',
# 'https://novabank.ng/careers/',
# 'https://novabank.ng/careers/nova-graduate-trainee-program/',
# 'https://novabank.ng/contact/',
# 'https://novabank.ng/self-service/',
# 'https://novabank.ng/whistle-blowing/',
# ]


llm = ChatOpenAI(
    model="gpt-4o-2024-11-20",
    temperature=0.2,
    timeout=None,
    max_retries=2,
)

async def setup_tools():
    loader = WebBaseLoader(
        web_paths=BANK_URLS,  
        verify_ssl=False,
        continue_on_failure=False,
        raise_for_status=False,
        requests_kwargs={"verify": False}
    )
    # loader = WebBaseLoader(web_paths=BANK_URLS,  
    #     verify_ssl=False,
    #     continue_on_failure=False,
    #     raise_for_status=False,
    #     requests_kwargs={"verify": False}
    # )
    # loader.requests_per_second = 1
    # docs = loader.aload()
    # docs

    docs = []
    for doc in loader.lazy_load():
        docs.append(doc)
    
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=800,
        length_function=len,
        chunk_overlap=100
    )
    split_docs = text_splitter.split_documents(docs)
    
    def remove_ws(d):
        text = d.page_content.replace('\n','')
        d.page_content = text
        return d
    clean_docs = [remove_ws(d) for d in split_docs]
    
    # Extract text content from documents
    texts = [doc.page_content for doc in clean_docs]
    
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-large", 
        chunk_size=1000,
        max_retries=2,
        show_progress_bar=True
    )

    
    # embeddings = HuggingFaceEmbeddings(
    #     model_name="all-MiniLM-L6-v2"
    #     # cache_folder="./model_cache",  # Cache models locally
    #     # model_kwargs={'device': 'cpu'}  # Force CPU usage if memory limited
    #     )
    # vectorstore = Chroma.from_documents(clean_docs, embeddings)
    # # Create vectorstore from texts
    vectorstore = InMemoryVectorStore.from_texts(
        texts=texts,
        embedding=embeddings,
    )

    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    rag_tool = create_retriever_tool(
        retriever,
        "info_rag",
        "Use this tool to answer user questions about GTI"
    )
    
    def tavily_search(query: str) -> str:
        """Use this to search for google map location and information on Akiba Bank"""
        search = TavilySearchResults(
            max_results=5,
            search_depth='advanced'
        )
        try:
            return search.invoke(query)
        except Exception as e:
            logger.error(f"Tavily search error: {str(e)}")
            return "Sorry, I couldn't perform the search at the moment."
    
    search_tool = Tool(
        name="live_search",
        description="Use this to search for google map location and information on Akiba Bank",
        func=tavily_search,
        args_schema=None
    )
    banking = BankingTools()
    banking_tools = banking.create_tools()
    all_tools = [search_tool, rag_tool] + banking_tools
    
    return all_tools 

# other_tools = BankingTools()
# small_tools = other_tools.create_small_tools()


class State(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    pin_verified: Optional[bool]




def create_graph(system_prompt: str, tools: List, phone_number: str,incoming_msg:str):
    """Create a new graph with the given system prompt and tools"""
    
    def chatbot(state: State):
        messages = [SystemMessage(content=system_prompt)] + state["messages"]
        response = llm.bind_tools(tools).invoke(messages)
        return {"messages": [response]}
    
    connection_kwargs = {
        "autocommit": True,
        "prepare_threshold": 0,
        "sslmode": "require",
        "connect_timeout": 30  # Add timeout
    }

    conninfo = f"postgresql://{db_username}:{db_password}@{db_host}:{db_port}/{db}"

    pool = ConnectionPool(
        conninfo=conninfo,
        min_size=2,  # Reduce initial pool size
        max_size=10, # Reduce max pool size
        kwargs=connection_kwargs,
        # timeout=30   # Add pool timeout
    )

    checkpointer = PostgresSaver(pool)
    # checkpointer.setup()
    builder = StateGraph(State)
    builder.add_node("chatbot", chatbot)
    
    # Add tool node
    tool_node = ToolNode(tools=tools)
    builder.add_node("tools", tool_node)
    
    # Add edges
    builder.add_conditional_edges(
        "chatbot",
        tools_condition,
    )
    builder.add_edge("tools", "chatbot")
    builder.add_edge(START, "chatbot")
        # Compile graph
    graph = builder.compile(
        checkpointer= checkpointer,
        store=in_memory_store
    )
    
    # Process with graph
    config = {"configurable": {"thread_id":phone_number, "user_id": phone_number,}}
    events = graph.stream(
        {"messages": [HumanMessage(content=incoming_msg)]},
        config,
        stream_mode="values"
    )
    response = None
    for event in events:
        if event.get("messages"):
            response = event["messages"][-1].content

    return response

async def send_webhook_transaction(transaction_data: dict):
    """Send transaction data to webhook with improved error handling"""
    try:
        async with httpx.AsyncClient(timeout=50.0) as client:
            logger.info(f"Sending webhook data: {transaction_data}")
            
            response = await client.post(
                f"{BACKEND_URL}/webhook",
                json=transaction_data,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "BankingApp/1.0"
                }
            )
            
            logger.info(f"Webhook response status: {response.status_code}")
            logger.info(f"Webhook response body: {response.text}")
            
            response.raise_for_status()
            return response

    except httpx.TimeoutException as e:
        error_msg = f"Webhook timeout: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=504, detail=error_msg)
        
    except httpx.RequestError as e:
        error_msg = f"Webhook request failed: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=502, detail=error_msg)
        
    except Exception as e:
        error_msg = f"Webhook error: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while sending webhook: {str(e)}"
        )



@app.post("/webhook")
async def webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    incoming_msg = ''
    try:
        content_type = request.headers.get('content-type', '')
        logger.info(f"Received content type: {content_type}")
        transaction_data = None
        form_data = None
        if 'application/json' in content_type:
            transaction_data = await request.json()
            logger.info(f"Received JSON data: {transaction_data}")
            if "customer_number" in transaction_data:
                customer_number = transaction_data['customer_number']
                phone_number = transaction_data['phone_number']
                incoming_msg = f"created account successfully,this is the customer number{customer_number}"
                logger.info(f"Received message from {phone_number}: {incoming_msg}")
                        # Get profile and generate response
                profile = await profile_service.fetch_customer_profile(phone_number)
                logger.info(f"Retrieved profile for {phone_number}: {profile.customer_type}")
                system_prompt = get_system_prompt(profile.dict())
                # graph = create_graph(system_prompt, tools)
                logger.info(f"transaction data{transaction_data}")
                # Process with graph
                response = create_graph(system_prompt, tools, phone_number, incoming_msg)
                logger.info(f"Generated response for {phone_number}: {response}")
                await send_whatsapp_message(phone_number, response)

                if transaction_data:
                    # Process your transaction logic here
                    return {"status": "success", "message": "Transaction processed"}
            else:
                incoming_msg = "I'm done, continue"
                phone_number ='+'+ transaction_data['mobile_number']
                logger.info(f"Received message from {phone_number}: {incoming_msg}")
                        # Get profile and generate response
                profile = await profile_service.fetch_customer_profile(phone_number)
                logger.info(f"Retrieved profile for {phone_number}: {profile.customer_type}")
                logger.info(f"Retrieved all customer profile {profile}")
                system_prompt = get_system_prompt(profile.dict())
                response = create_graph(system_prompt, tools, phone_number, incoming_msg)
                logger.info(f"Generated response for {phone_number}: {response}")
                await send_whatsapp_message(phone_number, response)

                if transaction_data:

                    return {"status": "success", "message": "Transaction processed"}
                
        elif 'application/x-www-form-urlencoded' in content_type or 'multipart/form-data' in content_type:
            form_data = await request.form()
            logger.info(f"Received form data: {form_data}")
            
            form_data = await request.form()
            logger.info(f"Received form data: {form_data}")
            
            phone_number = form_data.get('From', '').replace('whatsapp:', '')
            whatsapp_user = form_data.get("ProfileName")
            
            # Check if the message contains media (voice note)
            if 'MediaUrl0' in form_data and form_data.get('MediaContentType0', '').startswith('audio'):
                logger.info(f"Received voice message from {phone_number}")
                
                # Convert voice note to text using AssemblyAI
                media_url = form_data['MediaUrl0']
                media_url = form_data['MediaUrl0']
                media_type = form_data['MediaContentType0']
                print(f"Media URL: {media_url}\nMedia Content type: {media_type}")
                try:
                    # mp3_data = await ogg2mp3(media_url)

                    # mp3_buffer = io.BytesIO(mp3_data)
                    # mp3_buffer.seek(0) 
                    mp3_data = await ogg2mp3(media_url)
                    # mp3_data_google = await ogg_to_mp3_s3_url(media_url)
                    # logger.info(f"Converted voice note to mp3: {mp3_data_google}")
                    # loader = SpeechToTextLoader(project_id=PROJECT_ID, file_path=mp3_data_google)
    
                    # # Get the transcription results
                    # docs = loader.load()

                    # transcription_text = docs[0].page_content
                    # Create file object for OpenAI
                    file_obj = io.BytesIO(mp3_data)
                    file_obj.name = "audio.mp3"  # OpenAI needs filename
                    
                    transcription = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=file_obj
                    )
                    
                    incoming_msg = transcription.text
                    logger.info(f"Transcribed voice message: {incoming_msg}")
                except Exception as e:
                    logger.error(f"Voice processing error: {str(e)}")
                    await send_whatsapp_message(
                        phone_number, 
                        "I'm sorry, I couldn't process your voice message. Please try sending it again."
                    )
                    return ""


                # aai.settings.api_key = os.getenv("ASSEMBLY_AI_API_KEY")
                # transcriber = aai.Transcriber()
                # transcription = transcriber.transcribe(mp3_buffer)
                # transcription = client.audio.transcriptions.create(
                #     model="whisper-1", 
                #     file=mp3_data 
                # )

                # incoming_msg = transcription.text
                # logger.info(f"Transcribed voice message: {incoming_msg}")
                if not phone_number or not incoming_msg:
                    return ""
                    
                logger.info(f"Processing message from {phone_number}: {incoming_msg}")
                
                # Clear profile cache
                if phone_number in profile_service._profile_cache:
                    async with profile_service._cache_lock:
                        del profile_service._profile_cache[phone_number]
                        logger.info(f"Profile cache cleared for {phone_number}")

                # Get profile and generate response
                profile = await profile_service.fetch_customer_profile(phone_number)
                logger.info(f"Retrieved profile for {phone_number}: {profile.customer_type}")

                system_prompt = get_system_prompt(profile.dict())
                response = create_graph(system_prompt, tools, phone_number, incoming_msg)
                logger.info(f"Generated response for {phone_number}: {response}")                    
                if not response:
                    await send_whatsapp_message(phone_number, "I apologize, could you rephrase that?")
                    return ""
                    
                logger.info(f"Generated response for {phone_number}: {response}")
                
                # Send response
                await send_whatsapp_message(phone_number, response)
                
                # Background tasks

                # Add background tasks
                background_tasks.add_task(
                    process_background_tasks,
                    phone_number,
                    incoming_msg,
                    response,
                    profile,
                    whatsapp_user,
                    db  # Pass the db argument here
                )

            else:
                incoming_msg = form_data.get('Body', '').strip()
                
                if not phone_number or not incoming_msg:
                    return ""
                    
                logger.info(f"Processing message from {phone_number}: {incoming_msg}")
                
                if phone_number in profile_service._profile_cache:
                    async with profile_service._cache_lock:
                        del profile_service._profile_cache[phone_number]
                        logger.info(f"Profile cache cleared for {phone_number}")

                # Get profile and generate response
                profile = await profile_service.fetch_customer_profile(phone_number)
                logger.info(f"Retrieved profile for {phone_number}: {profile.customer_type}")
                logger.info(f"Retrieved all customer profile {profile}")
                logger.info(f"Retrieved all customer profile {type(profile)}")
                # customer_name = profile.customer_details['fullName'] #profile['customer_details']['fullName']
                system_prompt = get_system_prompt(profile.dict())
                response = create_graph(system_prompt, tools, phone_number, incoming_msg)
                logger.info(f"Generated response for {phone_number}: {response}")                       
                if not response:
                    await send_whatsapp_message(phone_number, "I apologize, could you rephrase that?")
                    return ""
                    
                logger.info(f"Generated response for {phone_number}: {response}")
                
                # Send response
                await send_whatsapp_message(phone_number, response)
                
                # Add background tasks
                background_tasks.add_task(
                    process_background_tasks,
                    phone_number,
                    incoming_msg,
                    response,
                    profile,
                    whatsapp_user,
                    db
                )

    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return ""


@app.get("/verify-pin", response_class=HTMLResponse)
async def verify_pin_page(request: Request):
    return templates.TemplateResponse("verify_pin.html", {"request": request})

@app.post("/api/verify-pin")
async def verify_pin(request: Request, pin_data: PinVerification, db: Session = Depends(get_db)):
    try:
        # Get the token from the query parameters
        token = request.query_params.get('token')
        if not token:
            return JSONResponse(
                status_code=400,
                content={"error": "Missing verification link"}
            )
            
        try:
            # Log the received token
            logger.info(f"Received token: {token}")
            
            # Decrypt token to get customer number and mobile number
            token_data = serializer.loads(token, max_age=120)
            logger.info(f"Decoded token data: {token_data}")
            
            customer_number = token_data['customer_number']
            mobile_number = token_data['mobile_number']
            
            # Log the decoded customer number and mobile number
            logger.info(f"Decoded customer_number: {customer_number}")
            logger.info(f"Decoded mobile_number: {mobile_number}")
            
            # Verify PIN
            async with httpx.AsyncClient() as session:
                verify_response = await session.post(
                    f"{VERIFY_URL}",
                    json={
                        "customer_number": customer_number,
                        "secure_pin": pin_data.secure_pin
                    }
                )
                
                logger.info(f"PIN verification status code: {verify_response.status_code}")
                logger.info(f"PIN verification response: {verify_response.text}")
                
                verify_data = verify_response.json()
                logger.info(f"PIN verification data: {verify_data}")  
                status = verify_data.get('status') 
                logger.info(f"status of the pin {status}")
                logger.info(f"status type of the pin {type(status)}")
                if status is not True:
                    return JSONResponse(
                        status_code=500,
                        content={"error": "You Entered the Wrong PIN. Please try again"}
                    )
                transaction_info = {
                    "timestamp": datetime.now().isoformat(),
                    "pin status": verify_data,
                    "mobile_number" : mobile_number
                }
                if verify_response.status_code != 200:
                    error_msg = verify_data.get("detail", "Verification failed, please try again")
                    logger.error(f"PIN verification failed: {error_msg}")
                    raise HTTPException(status_code=verify_response.status_code, detail=error_msg)
                
                # Check if PIN already exists for customer
                existing_pin = db.query(PinManagement).filter(
                    PinManagement.customer_number == customer_number
                ).first()
                logger.info(f'existing pin in db {existing_pin}')
                if existing_pin:
                    existing_pin.encrypted_pin = fernet.encrypt(pin_data.secure_pin.encode()).decode()
                    db.commit()
                else:
                    encrypted_pin = fernet.encrypt(pin_data.secure_pin.encode()).decode()
                    pin_record = PinManagement(
                        customer_number=customer_number,
                        encrypted_pin=encrypted_pin
                    )
                    logger.info(f'ecrypted pin stored in db{encrypted_pin}')
                    db.add(pin_record)
                    db.commit()
                    
                # Send to webhook
                await send_webhook_transaction(transaction_info)
    

                
                return {"status": "success", "message": "PIN sent successfully! Check your whatsapp"}
                
        except SignatureExpired:
            return JSONResponse(
                status_code=400, 
                content={"error": "Verification link has expired. Please request a new link"}
            )
        except BadSignature:
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid verification link, try requesting for another link"}
            )
            
    except Exception as e:
        logger.error(f"Error in PIN verification: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Unable to process your request. Please try again"}
        )



@app.get("/create-account", response_class=HTMLResponse)
async def create_account_page(request: Request):
    return template.TemplateResponse("form1.html", {"request": request})


@app.post("/api/account-creation-log")
async def log_account_creation(request: Request):
    try:
        # Get the raw JSON data
        data = await request.json()
        
        # Extract customer number (t24_customer_id) and phone number from the response
        customer_number = data.get('user', {}).get('t24_customer_id')
        phone_number = data.get('user', {}).get('phone_number')
        
        # Create transaction info
        transaction_info = {
            "timestamp": datetime.now().isoformat(),
            "customer_number": customer_number,
            "phone_number": phone_number
        }
        
        # Log the full response
        logger.info(f"Account creation response: {data}")
        
        # Send to webhook
        try:
            await send_webhook_transaction(transaction_info)
            logger.info(f"Webhook sent successfully: {transaction_info}")
        except Exception as webhook_error:
            logger.error(f"Webhook error: {str(webhook_error)}")
            logger.error(f"Failed transaction info: {transaction_info}")
        
        return {"message": "Log recorded successfully"}
        
    except Exception as e:
        logger.error(f"Error processing account creation log: {str(e)}")
        return {"message": "Error recording log", "error": str(e)}
    


@app.on_event("startup")
async def startup_event():
    """Initialize services and RAG on startup"""
    global tools
    tools = await setup_tools()
    logger.info("Application started, RAG tools initialized")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await profile_service.close()
    await memory_service.close()
    logger.info("Application shutdown, resources cleaned up")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8037, reload=True,log_level="debug")
