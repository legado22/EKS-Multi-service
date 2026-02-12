from pydantic_settings import BaseSettings
from typing import Dict
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # API Gateway
    app_name: str = "Execute Tech Academy - API Gateway"
    version: str = "1.0.0"
    debug: bool = True
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    
    # Service URLs
    auth_service_url: str = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001")
    product_service_url: str = os.getenv("PRODUCT_SERVICE_URL", "http://product-service:8002")
    order_service_url: str = os.getenv("ORDER_SERVICE_URL", "http://order-service:8003")
    payment_service_url: str = os.getenv("PAYMENT_SERVICE_URL", "http://payment-service:8004")
    
    # Redis (for caching and rate limiting)
    redis_host: str = os.getenv("REDIS_HOST", "redis")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_db: int = 0
    
    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 60
    
    # CORS
    cors_origins: list = ["*"]
    
    # Circuit Breaker
    circuit_breaker_enabled: bool = True
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_timeout: int = 60
    
    class Config:
        env_file = ".env"

settings = Settings()

# Service route mapping
SERVICE_ROUTES: Dict[str, str] = {
    "/auth": settings.auth_service_url,
    "/products": settings.product_service_url,
    "/instructors": settings.product_service_url,
    "/courses": settings.product_service_url,
    "/modules": settings.product_service_url,
    "/lessons": settings.product_service_url,
    "/orders": settings.order_service_url,
    "/enrollments": settings.order_service_url,
    "/cart": settings.order_service_url,
    "/progress": settings.order_service_url,
    "/reviews": settings.order_service_url,
    "/payments": settings.payment_service_url,
    "/invoices": settings.payment_service_url,
    "/refunds": settings.payment_service_url,
    "/wallet": settings.payment_service_url,
}
