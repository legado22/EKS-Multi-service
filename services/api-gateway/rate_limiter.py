from fastapi import HTTPException, status, Request
import redis
import time
from config import settings

class RateLimiter:
    def __init__(self):
        if settings.rate_limit_enabled:
            try:
                self.redis_client = redis.Redis(
                    host=settings.redis_host,
                    port=settings.redis_port,
                    db=settings.redis_db,
                    decode_responses=True
                )
                self.redis_client.ping()
                self.enabled = True
            except Exception as e:
                print(f"Redis connection failed: {e}. Rate limiting disabled.")
                self.enabled = False
        else:
            self.enabled = False
    
    async def check_rate_limit(self, request: Request, identifier: str = None):
        """Check if request is within rate limit"""
        if not self.enabled:
            return
        
        # Use IP address if no identifier provided
        if not identifier:
            identifier = request.client.host
        
        key = f"rate_limit:{identifier}"
        current_time = int(time.time())
        window = 60  # 1 minute window
        
        try:
            # Get current count
            count = self.redis_client.get(key)
            
            if count is None:
                # First request in window
                self.redis_client.setex(key, window, 1)
            else:
                count = int(count)
                if count >= settings.rate_limit_per_minute:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Rate limit exceeded. Please try again later."
                    )
                else:
                    self.redis_client.incr(key)
        except redis.RedisError as e:
            print(f"Redis error in rate limiter: {e}")
            # Continue without rate limiting if Redis fails

rate_limiter = RateLimiter()
