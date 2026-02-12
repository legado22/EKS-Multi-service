from fastapi import HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from typing import Optional
from config import settings

security = HTTPBearer()

class AuthMiddleware:
    def __init__(self):
        self.secret_key = settings.secret_key
        self.algorithm = settings.algorithm
    
    async def verify_token(self, credentials: HTTPAuthorizationCredentials) -> dict:
        """Verify JWT token"""
        token = credentials.credentials
        
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id: str = payload.get("sub")
            role: str = payload.get("role")
            
            if user_id is None:
                raise credentials_exception
                
            return {
                "user_id": int(user_id),
                "role": role,
                "token": token
            }
        except JWTError:
            raise credentials_exception
    
    def get_token_from_request(self, request: Request) -> Optional[str]:
        """Extract token from request headers"""
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header.split(" ")[1]
        return None

auth_middleware = AuthMiddleware()
