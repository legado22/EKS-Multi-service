import httpx
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

class PaystackGateway:
    """Paystack payment gateway integration (Popular in Nigeria)"""
    
    def __init__(self):
        self.secret_key = os.getenv("PAYSTACK_SECRET_KEY", "")
        self.public_key = os.getenv("PAYSTACK_PUBLIC_KEY", "")
        self.base_url = "https://api.paystack.co"
    
    async def initialize_transaction(
        self, 
        email: str, 
        amount: float, 
        reference: str,
        callback_url: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Initialize a Paystack transaction"""
        url = f"{self.base_url}/transaction/initialize"
        
        # Paystack amount is in kobo (smallest currency unit)
        amount_in_kobo = int(amount * 100)
        
        headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "email": email,
            "amount": amount_in_kobo,
            "reference": reference,
            "callback_url": callback_url,
            "metadata": metadata or {}
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data, headers=headers)
            return response.json()
    
    async def verify_transaction(self, reference: str) -> Dict[str, Any]:
        """Verify a Paystack transaction"""
        url = f"{self.base_url}/transaction/verify/{reference}"
        
        headers = {
            "Authorization": f"Bearer {self.secret_key}"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            return response.json()
    
    async def create_refund(self, transaction_id: str, amount: Optional[float] = None) -> Dict[str, Any]:
        """Create a refund for a transaction"""
        url = f"{self.base_url}/refund"
        
        headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }
        
        data = {"transaction": transaction_id}
        if amount:
            data["amount"] = int(amount * 100)  # Convert to kobo
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data, headers=headers)
            return response.json()

class FlutterwaveGateway:
    """Flutterwave payment gateway integration (Popular in Africa)"""
    
    def __init__(self):
        self.secret_key = os.getenv("FLUTTERWAVE_SECRET_KEY", "")
        self.public_key = os.getenv("FLUTTERWAVE_PUBLIC_KEY", "")
        self.base_url = "https://api.flutterwave.com/v3"
    
    async def initialize_payment(
        self,
        amount: float,
        currency: str,
        email: str,
        tx_ref: str,
        redirect_url: str,
        customer_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Initialize a Flutterwave payment"""
        url = f"{self.base_url}/payments"
        
        headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "tx_ref": tx_ref,
            "amount": amount,
            "currency": currency,
            "redirect_url": redirect_url,
            "customer": {
                "email": email,
                "name": customer_name
            },
            "customizations": {
                "title": "Execute Tech Academy",
                "description": "Course Payment",
                "logo": ""
            },
            "meta": metadata or {}
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data, headers=headers)
            return response.json()
    
    async def verify_transaction(self, transaction_id: str) -> Dict[str, Any]:
        """Verify a Flutterwave transaction"""
        url = f"{self.base_url}/transactions/{transaction_id}/verify"
        
        headers = {
            "Authorization": f"Bearer {self.secret_key}"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            return response.json()

class StripeGateway:
    """Stripe payment gateway integration (International)"""
    
    def __init__(self):
        self.secret_key = os.getenv("STRIPE_SECRET_KEY", "")
        self.publishable_key = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    
    # Stripe integration would use their official SDK
    # This is a placeholder for the structure

def get_payment_gateway(gateway_name: str):
    """Factory function to get payment gateway"""
    gateways = {
        "paystack": PaystackGateway,
        "flutterwave": FlutterwaveGateway,
        "stripe": StripeGateway
    }
    
    gateway_class = gateways.get(gateway_name.lower())
    if not gateway_class:
        raise ValueError(f"Unsupported payment gateway: {gateway_name}")
    
    return gateway_class()
