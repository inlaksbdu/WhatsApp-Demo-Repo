from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from .config.settings import settings

# Import all routers
from .api.v1.conversations.router import router as conversations_router
from .api.v1.customers.router import router as customers_router
from .api.v1.sentiment.router import router as sentiment_router
from .api.v1.complaints.router import router as complaints_router
from .api.v1.bank_requests.router import router as bank_requests_router
from .api.v1.transfers.router import router as transfers_router

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for banking chatbot analytics dashboard",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(conversations_router, prefix="/api/v1")
app.include_router(customers_router, prefix="/api/v1")
app.include_router(sentiment_router, prefix="/api/v1")
app.include_router(complaints_router, prefix="/api/v1")
app.include_router(bank_requests_router, prefix="/api/v1")
app.include_router(transfers_router, prefix="/api/v1")

@app.get("/", tags=["Health Check"])
async def health_check():
    """
    Health check endpoint to verify the API is running
    """
    return {
        "status": "healthy",
        "message": "Banking chatbot analytics API is running"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG_MODE
    ) 