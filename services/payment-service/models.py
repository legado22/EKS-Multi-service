from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum

class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"

class PaymentMethod(str, enum.Enum):
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"
    PAYPAL = "paypal"
    STRIPE = "stripe"
    PAYSTACK = "paystack"  # Popular in Nigeria
    FLUTTERWAVE = "flutterwave"  # Popular in Africa

class RefundStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(String, unique=True, nullable=False, index=True)
    order_id = Column(Integer, nullable=False, index=True)  # References order service
    student_id = Column(Integer, nullable=False, index=True)  # References auth service
    amount = Column(Float, nullable=False)
    currency = Column(String, default="NGN")  # Nigerian Naira
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    
    # Payment gateway details
    gateway_transaction_id = Column(String, index=True)
    gateway_reference = Column(String)
    gateway_response = Column(JSON)
    
    # Metadata
    description = Column(Text)
    metadata = Column(JSON)
    
    # Timestamps
    paid_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    transactions = relationship("Transaction", back_populates="payment", cascade="all, delete-orphan")
    refunds = relationship("Refund", back_populates="payment", cascade="all, delete-orphan")
    invoice = relationship("Invoice", back_populates="payment", uselist=False)

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=False)
    transaction_type = Column(String, nullable=False)  # charge, refund, capture
    amount = Column(Float, nullable=False)
    status = Column(Enum(PaymentStatus), nullable=False)
    gateway_transaction_id = Column(String)
    gateway_response = Column(JSON)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    payment = relationship("Payment", back_populates="transactions")

class Refund(Base):
    __tablename__ = "refunds"

    id = Column(Integer, primary_key=True, index=True)
    refund_id = Column(String, unique=True, nullable=False, index=True)
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=False)
    amount = Column(Float, nullable=False)
    reason = Column(Text)
    status = Column(Enum(RefundStatus), default=RefundStatus.PENDING, nullable=False)
    gateway_refund_id = Column(String)
    gateway_response = Column(JSON)
    requested_by = Column(Integer, nullable=False)  # User ID who requested
    processed_by = Column(Integer)  # Admin who processed
    requested_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True))
    
    # Relationships
    payment = relationship("Payment", back_populates="refunds")

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String, unique=True, nullable=False, index=True)
    payment_id = Column(Integer, ForeignKey("payments.id"), unique=True, nullable=False)
    order_id = Column(Integer, nullable=False, index=True)
    student_id = Column(Integer, nullable=False, index=True)
    
    # Invoice details
    subtotal = Column(Float, nullable=False)
    tax = Column(Float, default=0.0)
    discount = Column(Float, default=0.0)
    total = Column(Float, nullable=False)
    currency = Column(String, default="NGN")
    
    # Billing info
    billing_name = Column(String, nullable=False)
    billing_email = Column(String, nullable=False)
    billing_address = Column(Text)
    billing_city = Column(String)
    billing_state = Column(String)
    billing_country = Column(String, default="Nigeria")
    
    # Items
    items = Column(JSON)  # List of invoice items
    
    # URLs
    pdf_url = Column(String)
    
    # Status
    is_paid = Column(Boolean, default=False)
    paid_at = Column(DateTime(timezone=True))
    due_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    payment = relationship("Payment", back_populates="invoice")

class PaymentGatewayConfig(Base):
    __tablename__ = "payment_gateway_configs"

    id = Column(Integer, primary_key=True, index=True)
    gateway_name = Column(String, unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    is_test_mode = Column(Boolean, default=True)
    public_key = Column(String)
    secret_key = Column(String)
    webhook_secret = Column(String)
    config = Column(JSON)  # Additional gateway-specific config
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, unique=True, nullable=False, index=True)
    balance = Column(Float, default=0.0)
    currency = Column(String, default="NGN")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    transactions = relationship("WalletTransaction", back_populates="wallet")

class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"

    id = Column(Integer, primary_key=True, index=True)
    wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=False)
    transaction_type = Column(String, nullable=False)  # credit, debit
    amount = Column(Float, nullable=False)
    balance_before = Column(Float, nullable=False)
    balance_after = Column(Float, nullable=False)
    description = Column(Text)
    reference = Column(String, index=True)
    metadata = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    wallet = relationship("Wallet", back_populates="transactions")
