from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from models import PaymentStatus, PaymentMethod, RefundStatus

# Payment Schemas
class PaymentCreate(BaseModel):
    order_id: int
    amount: float
    currency: str = "NGN"
    payment_method: PaymentMethod
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class PaymentUpdate(BaseModel):
    status: Optional[PaymentStatus] = None
    gateway_transaction_id: Optional[str] = None
    gateway_reference: Optional[str] = None
    gateway_response: Optional[Dict[str, Any]] = None

class PaymentResponse(BaseModel):
    id: int
    payment_id: str
    order_id: int
    student_id: int
    amount: float
    currency: str
    status: PaymentStatus
    payment_method: PaymentMethod
    gateway_transaction_id: Optional[str]
    gateway_reference: Optional[str]
    description: Optional[str]
    paid_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Transaction Schemas
class TransactionResponse(BaseModel):
    id: int
    payment_id: int
    transaction_type: str
    amount: float
    status: PaymentStatus
    gateway_transaction_id: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Refund Schemas
class RefundCreate(BaseModel):
    payment_id: int
    amount: float
    reason: Optional[str] = None

class RefundUpdate(BaseModel):
    status: Optional[RefundStatus] = None
    gateway_refund_id: Optional[str] = None
    gateway_response: Optional[Dict[str, Any]] = None

class RefundResponse(BaseModel):
    id: int
    refund_id: str
    payment_id: int
    amount: float
    reason: Optional[str]
    status: RefundStatus
    requested_by: int
    processed_by: Optional[int]
    requested_at: datetime
    processed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# Invoice Schemas
class InvoiceCreate(BaseModel):
    payment_id: int
    order_id: int
    subtotal: float
    tax: float = 0.0
    discount: float = 0.0
    billing_name: str
    billing_email: EmailStr
    billing_address: Optional[str] = None
    billing_city: Optional[str] = None
    billing_state: Optional[str] = None
    billing_country: str = "Nigeria"
    items: List[Dict[str, Any]]

class InvoiceResponse(BaseModel):
    id: int
    invoice_number: str
    payment_id: int
    order_id: int
    student_id: int
    subtotal: float
    tax: float
    discount: float
    total: float
    currency: str
    billing_name: str
    billing_email: str
    is_paid: bool
    paid_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Wallet Schemas
class WalletResponse(BaseModel):
    id: int
    student_id: int
    balance: float
    currency: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class WalletTransactionCreate(BaseModel):
    amount: float
    transaction_type: str  # credit or debit
    description: Optional[str] = None
    reference: Optional[str] = None

class WalletTransactionResponse(BaseModel):
    id: int
    wallet_id: int
    transaction_type: str
    amount: float
    balance_before: float
    balance_after: float
    description: Optional[str]
    reference: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Payment Gateway Schemas
class PaymentInitiateRequest(BaseModel):
    order_id: int
    amount: float
    payment_method: PaymentMethod = PaymentMethod.PAYSTACK
    callback_url: str
    metadata: Optional[Dict[str, Any]] = None

class PaymentInitiateResponse(BaseModel):
    payment_id: str
    authorization_url: str
    access_code: str
    reference: str

class PaymentVerifyResponse(BaseModel):
    payment_id: str
    status: PaymentStatus
    amount: float
    paid_at: Optional[datetime]
    gateway_response: Optional[Dict[str, Any]]
