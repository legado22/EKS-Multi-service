from circuitbreaker import circuit
from typing import Callable
import httpx
from config import settings

class ServiceCircuitBreaker:
    """Circuit breaker to prevent cascading failures"""
    
    @staticmethod
    @circuit(
        failure_threshold=settings.circuit_breaker_failure_threshold,
        recovery_timeout=settings.circuit_breaker_timeout,
        expected_exception=httpx.HTTPError
    )
    async def call_service(func: Callable, *args, **kwargs):
        """Wrap service calls with circuit breaker"""
        return await func(*args, **kwargs)

circuit_breaker = ServiceCircuitBreaker()
