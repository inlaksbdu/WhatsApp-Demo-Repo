import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Project settings
    PROJECT_NAME: str = "Banking Chatbot Analytics API"
    API_PREFIX: str = "/api/v1"
    DEBUG_MODE: bool = os.getenv("DEBUG_MODE", "True") == "True"
    
    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8019"))
    
    # Database settings
    DB_DRIVERNAME: str = os.getenv("DB_DRIVERNAME", "postgresql")
    DB_USERNAME: str = os.getenv("DB_USERNAME", "neondb_owner")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "npg_d1oXhVAzCaf6")
    DB_HOST: str = os.getenv("DB_HOST", "ep-twilight-frost-a5x46mrr-pooler.us-east-2.aws.neon.tech")
    DB_NAME: str = os.getenv("DB_NAME", "neondb")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    
    # Twilio settings
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_NUMBER: str = os.getenv("TWILIO_NUMBER", "")
    TWILIO_NUM: str = os.getenv("TWILIO_NUM", "")
    
    # OpenAI settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Other API keys
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")
    HF_TOKEN: str = os.getenv("HF_TOKEN", "")
    LANGCHAIN_API_KEY: str = os.getenv("LANGCHAIN_API_KEY", "")
    ASSEMBLY_AI_API_KEY: str = os.getenv("ASSEMBLY_AI_API_KEY", "")
    
    # Email settings
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    FROM_EMAIL: str = os.getenv("FROM_EMAIL", "")
    
    # URLs
    BACKEND_URL: str = os.getenv("BACKEND_URL", "")
    BASE_URL: str = os.getenv("BASE_URL", "")
    VERIFY_URL: str = os.getenv("VERIFY_URL", "")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    secret: str = os.getenv("secret", "")
    
    # CORS settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://banking-chatbot-analytics.example.com",
    ]
    
    @property
    def DATABASE_URL(self) -> str:
        """Construct database URL from components"""
        return f"{self.DB_DRIVERNAME}://{self.DB_USERNAME}:{self.DB_PASSWORD}@{self.DB_HOST}/{self.DB_NAME}?sslmode=require"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings() 