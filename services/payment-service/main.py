from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import uuid
import httpx

import models
import schemas
from database import engine, get_db
from auth_middleware import verify_token, verify_admin
from payment_gateways import get_payment_gateway, PaystackGateway

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Execute Tech Academy - Payment Service",
    description="Payment Processing and Invoice Management Service",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "service": "Payment Service",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# ==================== PAYMENT ENDPOINTS ====================

async def notify_order_service(order_id: int, payment_status: str):
    """Notify order service about payment status"""
    try:
        order_service_url = "http://order-service:8003"  # Update with actual URL
        async with httpx.AsyncClient() as client:
            await client.put(
                f"{order_service_url}/orders/{order_id}",
                json={"status": "confirmed" if payment_status == "completed" else "failed"}
            )
    except Exception as e:
        print(f"Failed to notify order service: {e}")

@app.post("/payments/initiate", response_model=schemas.PaymentInitiateResponse)
async def initiate_payment(
    request: schemas.PaymentInitiateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """Initiate a payment with selected gateway"""
    
    # Generate payment reference
    payment_reference = f"PAY-{uuid.uuid4().hex[:12].upper()}"
    
    # Create payment record
    db_payment = models.Payment(
        payment_id=payment_reference,
        order_id=request.order_id,
        student_id=current_user["user_id"],
        amount=request.amount,
        payment_method=request.payment_method,
        status=models.PaymentStatus.PENDING,
        expires_at=datetime.utcnow() + timedelta(hours=1),
        metadata=request.metadata
    )
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    
    # Initialize with payment gateway
    try:
        gateway = get_payment_gateway(request.payment_method.value)
        
        if isinstance(gateway, PaystackGateway):
            # Get user email (would normally fetch from auth service)
            user_email = f"student{current_user['user_id']}@executetechacademy.com"
            
            result = await gateway.initialize_transaction(
                email=user_email,
                amount=request.amount,
                reference=payment_reference,
                callback_url=request.callback_url,
                metadata=request.metadata
            )
            
            if result.get("status"):
                data = result.get("data", {})
                return {
                    "payment_id": payment_reference,
                    "authorization_url": data.get("authorization_url", ""),
                    "access_code": data.get("access_code", ""),
                    "reference": payment_reference
                }
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize payment"
        )
        
    except Exception as e:
        db_payment.status = models.PaymentStatus.FAILED
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Payment initialization failed: {str(e)}"
        )

@app.get("/payments/verify/{payment_id}", response_model=schemas.PaymentVerifyResponse)
async def verify_payment(
    payment_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """Verify a payment"""
    
    payment = db.query(models.Payment).filter(
        models.Payment.payment_id == payment_id
    ).first()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    # Verify with payment gateway
    try:
        gateway = get_payment_gateway(payment.payment_method.value)
        
        if isinstance(gateway, PaystackGateway):
            result = await gateway.verify_transaction(payment_id)
            
            if result.get("status") and result.get("data"):
                data = result["data"]
                
                if data.get("status") == "success":
                    payment.status = models.PaymentStatus.COMPLETED
                    payment.paid_at = datetime.utcnow()
                    payment.gateway_transaction_id = str(data.get("id"))
                    payment.gateway_response = data
                    
                    # Create transaction record
                    transaction = models.Transaction(
                        payment_id=payment.id,
                        transaction_type="charge",
                        amount=payment.amount,
                        status=models.PaymentStatus.COMPLETED,
                        gateway_transaction_id=str(data.get("id")),
                        gateway_response=data
                    )
                    db.add(transaction)
                    
                    # Notify order service
                    background_tasks.add_task(
                        notify_order_service,
                        payment.order_id,
                        "completed"
                    )
                else:
                    payment.status = models.PaymentStatus.FAILED
        
        db.commit()
        db.refresh(payment)
        
        return {
            "payment_id": payment.payment_id,
            "status": payment.status,
            "amount": payment.amount,
            "paid_at": payment.paid_at,
            "gateway_response": payment.gateway_response
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Payment verification failed: {str(e)}"
        )

@app.post("/payments", response_model=schemas.PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(
    payment: schemas.PaymentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """Create a payment record"""
    payment_id = f"PAY-{uuid.uuid4().hex[:12].upper()}"
    
    db_payment = models.Payment(
        payment_id=payment_id,
        order_id=payment.order_id,
        student_id=current_user["user_id"],
        amount=payment.amount,
        currency=payment.currency,
        payment_method=payment.payment_method,
        description=payment.description,
        metadata=payment.metadata,
        expires_at=datetime.utcnow() + timedelta(hours=1)
    )
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment

@app.get("/payments", response_model=List[schemas.PaymentResponse])
def list_payments(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    if current_user["role"] == "admin":
        payments = db.query(models.Payment).offset(skip).limit(limit).all()
    else:
        payments = db.query(models.Payment).filter(
            models.Payment.student_id == current_user["user_id"]
        ).offset(skip).limit(limit).all()
    
    return payments

@app.get("/payments/{payment_id}", response_model=schemas.PaymentResponse)
def get_payment(
    payment_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    payment = db.query(models.Payment).filter(
        models.Payment.payment_id == payment_id
    ).first()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    if current_user["role"] != "admin" and payment.student_id != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return payment

@app.put("/payments/{payment_id}", response_model=schemas.PaymentResponse)
def update_payment(
    payment_id: str,
    payment_update: schemas.PaymentUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_admin)
):
    payment = db.query(models.Payment).filter(
        models.Payment.payment_id == payment_id
    ).first()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    for key, value in payment_update.dict(exclude_unset=True).items():
        setattr(payment, key, value)
    
    if payment_update.status == models.PaymentStatus.COMPLETED and not payment.paid_at:
        payment.paid_at = datetime.utcnow()
    
    db.commit()
    db.refresh(payment)
    return payment

# ==================== REFUND ENDPOINTS ====================

@app.post("/refunds", response_model=schemas.RefundResponse, status_code=status.HTTP_201_CREATED)
def create_refund(
    refund: schemas.RefundCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    payment = db.query(models.Payment).filter(
        models.Payment.id == refund.payment_id
    ).first()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    if current_user["role"] != "admin" and payment.student_id != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    refund_id = f"REF-{uuid.uuid4().hex[:12].upper()}"
    
    db_refund = models.Refund(
        refund_id=refund_id,
        payment_id=refund.payment_id,
        amount=refund.amount,
        reason=refund.reason,
        requested_by=current_user["user_id"]
    )
    db.add(db_refund)
    db.commit()
    db.refresh(db_refund)
    return db_refund

@app.get("/refunds", response_model=List[schemas.RefundResponse])
def list_refunds(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_admin)
):
    refunds = db.query(models.Refund).offset(skip).limit(limit).all()
    return refunds

@app.put("/refunds/{refund_id}", response_model=schemas.RefundResponse)
def process_refund(
    refund_id: str,
    refund_update: schemas.RefundUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_admin)
):
    refund = db.query(models.Refund).filter(
        models.Refund.refund_id == refund_id
    ).first()
    
    if not refund:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Refund not found"
        )
    
    for key, value in refund_update.dict(exclude_unset=True).items():
        setattr(refund, key, value)
    
    refund.processed_by = current_user["user_id"]
    refund.processed_at = datetime.utcnow()
    
    if refund_update.status == models.RefundStatus.COMPLETED:
        payment = db.query(models.Payment).filter(
            models.Payment.id == refund.payment_id
        ).first()
        payment.status = models.PaymentStatus.REFUNDED
    
    db.commit()
    db.refresh(refund)
    return refund

# ==================== INVOICE ENDPOINTS ====================

@app.post("/invoices", response_model=schemas.InvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_invoice(
    invoice: schemas.InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    invoice_number = f"INV-{uuid.uuid4().hex[:10].upper()}"
    
    total = invoice.subtotal + invoice.tax - invoice.discount
    
    db_invoice = models.Invoice(
        invoice_number=invoice_number,
        payment_id=invoice.payment_id,
        order_id=invoice.order_id,
        student_id=current_user["user_id"],
        subtotal=invoice.subtotal,
        tax=invoice.tax,
        discount=invoice.discount,
        total=total,
        billing_name=invoice.billing_name,
        billing_email=invoice.billing_email,
        billing_address=invoice.billing_address,
        billing_city=invoice.billing_city,
        billing_state=invoice.billing_state,
        billing_country=invoice.billing_country,
        items=invoice.items
    )
    db.add(db_invoice)
    db.commit()
    db.refresh(db_invoice)
    return db_invoice

@app.get("/invoices", response_model=List[schemas.InvoiceResponse])
def list_invoices(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    if current_user["role"] == "admin":
        invoices = db.query(models.Invoice).offset(skip).limit(limit).all()
    else:
        invoices = db.query(models.Invoice).filter(
            models.Invoice.student_id == current_user["user_id"]
        ).offset(skip).limit(limit).all()
    
    return invoices

@app.get("/invoices/{invoice_number}", response_model=schemas.InvoiceResponse)
def get_invoice(
    invoice_number: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    invoice = db.query(models.Invoice).filter(
        models.Invoice.invoice_number == invoice_number
    ).first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    if current_user["role"] != "admin" and invoice.student_id != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return invoice

# ==================== WALLET ENDPOINTS ====================

@app.get("/wallet", response_model=schemas.WalletResponse)
def get_wallet(
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    wallet = db.query(models.Wallet).filter(
        models.Wallet.student_id == current_user["user_id"]
    ).first()
    
    if not wallet:
        # Create wallet if doesn't exist
        wallet = models.Wallet(student_id=current_user["user_id"])
        db.add(wallet)
        db.commit()
        db.refresh(wallet)
    
    return wallet

@app.get("/wallet/transactions", response_model=List[schemas.WalletTransactionResponse])
def get_wallet_transactions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    wallet = db.query(models.Wallet).filter(
        models.Wallet.student_id == current_user["user_id"]
    ).first()
    
    if not wallet:
        return []
    
    transactions = db.query(models.WalletTransaction).filter(
        models.WalletTransaction.wallet_id == wallet.id
    ).offset(skip).limit(limit).all()
    
    return transactions

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
