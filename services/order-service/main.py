from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import uuid

import models
import schemas
from database import engine, get_db
from auth_middleware import verify_token, verify_admin

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Execute Tech Academy - Order Service",
    description="Enrollment and Order Management Service",
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
        "service": "Order Service",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# ==================== CART ENDPOINTS ====================

@app.get("/cart", response_model=schemas.CartResponse)
def get_cart(
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    cart = db.query(models.Cart).filter(
        models.Cart.student_id == current_user["user_id"]
    ).first()
    
    if not cart:
        # Create cart if doesn't exist
        cart = models.Cart(student_id=current_user["user_id"])
        db.add(cart)
        db.commit()
        db.refresh(cart)
    
    return cart

@app.post("/cart/items", response_model=schemas.CartItemResponse, status_code=status.HTTP_201_CREATED)
def add_to_cart(
    item: schemas.CartItemCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    # Get or create cart
    cart = db.query(models.Cart).filter(
        models.Cart.student_id == current_user["user_id"]
    ).first()
    
    if not cart:
        cart = models.Cart(student_id=current_user["user_id"])
        db.add(cart)
        db.commit()
        db.refresh(cart)
    
    # Check if already enrolled
    enrollment = db.query(models.Enrollment).filter(
        models.Enrollment.student_id == current_user["user_id"],
        models.Enrollment.course_id == item.course_id
    ).first()
    
    if enrollment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already enrolled in this course"
        )
    
    # Check if already in cart
    existing_item = db.query(models.CartItem).filter(
        models.CartItem.cart_id == cart.id,
        models.CartItem.course_id == item.course_id
    ).first()
    
    if existing_item:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Course already in cart"
        )
    
    cart_item = models.CartItem(
        cart_id=cart.id,
        course_id=item.course_id
    )
    db.add(cart_item)
    db.commit()
    db.refresh(cart_item)
    return cart_item

@app.delete("/cart/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_cart(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    cart = db.query(models.Cart).filter(
        models.Cart.student_id == current_user["user_id"]
    ).first()
    
    if not cart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found"
        )
    
    cart_item = db.query(models.CartItem).filter(
        models.CartItem.id == item_id,
        models.CartItem.cart_id == cart.id
    ).first()
    
    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found in cart"
        )
    
    db.delete(cart_item)
    db.commit()
    return None

@app.delete("/cart", status_code=status.HTTP_204_NO_CONTENT)
def clear_cart(
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    cart = db.query(models.Cart).filter(
        models.Cart.student_id == current_user["user_id"]
    ).first()
    
    if cart:
        db.query(models.CartItem).filter(models.CartItem.cart_id == cart.id).delete()
        db.commit()
    
    return None

# ==================== ORDER ENDPOINTS ====================

@app.post("/orders", response_model=schemas.OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    order: schemas.OrderCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    # Calculate totals
    total_amount = sum(item["price"] for item in order.items)
    final_amount = total_amount - order.discount_amount
    
    # Generate order number
    order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
    
    # Create order
    db_order = models.Order(
        order_number=order_number,
        student_id=current_user["user_id"],
        total_amount=total_amount,
        discount_amount=order.discount_amount,
        final_amount=final_amount,
        notes=order.notes
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    
    # Create order items
    for item in order.items:
        order_item = models.OrderItem(
            order_id=db_order.id,
            course_id=item["course_id"],
            course_title=item["title"],
            price=item["price"],
            discount=0.0,
            final_price=item["price"]
        )
        db.add(order_item)
    
    db.commit()
    db.refresh(db_order)
    return db_order

@app.get("/orders", response_model=List[schemas.OrderResponse])
def list_orders(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    if current_user["role"] == "admin":
        # Admins can see all orders
        orders = db.query(models.Order).offset(skip).limit(limit).all()
    else:
        # Students see only their orders
        orders = db.query(models.Order).filter(
            models.Order.student_id == current_user["user_id"]
        ).offset(skip).limit(limit).all()
    
    return orders

@app.get("/orders/{order_id}", response_model=schemas.OrderResponse)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Check permissions
    if current_user["role"] != "admin" and order.student_id != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return order

@app.put("/orders/{order_id}", response_model=schemas.OrderResponse)
def update_order(
    order_id: int,
    order_update: schemas.OrderUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_admin)
):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    for key, value in order_update.dict(exclude_unset=True).items():
        setattr(order, key, value)
    
    # If order is confirmed, create enrollments
    if order_update.status == models.OrderStatus.CONFIRMED and order.status != models.OrderStatus.CONFIRMED:
        for item in order.items:
            # Check if enrollment already exists
            existing = db.query(models.Enrollment).filter(
                models.Enrollment.student_id == order.student_id,
                models.Enrollment.course_id == item.course_id
            ).first()
            
            if not existing:
                enrollment = models.Enrollment(
                    student_id=order.student_id,
                    course_id=item.course_id,
                    order_id=order.id,
                    status=models.EnrollmentStatus.ACTIVE
                )
                db.add(enrollment)
    
    db.commit()
    db.refresh(order)
    return order

# ==================== ENROLLMENT ENDPOINTS ====================

@app.post("/enrollments", response_model=schemas.EnrollmentResponse, status_code=status.HTTP_201_CREATED)
def create_enrollment(
    enrollment: schemas.EnrollmentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    # Check if already enrolled
    existing = db.query(models.Enrollment).filter(
        models.Enrollment.student_id == current_user["user_id"],
        models.Enrollment.course_id == enrollment.course_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already enrolled in this course"
        )
    
    db_enrollment = models.Enrollment(
        student_id=current_user["user_id"],
        course_id=enrollment.course_id,
        order_id=enrollment.order_id,
        status=models.EnrollmentStatus.ACTIVE
    )
    db.add(db_enrollment)
    db.commit()
    db.refresh(db_enrollment)
    return db_enrollment

@app.get("/enrollments", response_model=List[schemas.EnrollmentResponse])
def list_enrollments(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    if current_user["role"] == "admin":
        enrollments = db.query(models.Enrollment).offset(skip).limit(limit).all()
    else:
        enrollments = db.query(models.Enrollment).filter(
            models.Enrollment.student_id == current_user["user_id"]
        ).offset(skip).limit(limit).all()
    
    return enrollments

@app.get("/enrollments/{enrollment_id}", response_model=schemas.EnrollmentResponse)
def get_enrollment(
    enrollment_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    enrollment = db.query(models.Enrollment).filter(
        models.Enrollment.id == enrollment_id
    ).first()
    
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment not found"
        )
    
    # Check permissions
    if current_user["role"] != "admin" and enrollment.student_id != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return enrollment

@app.get("/courses/{course_id}/enrollment", response_model=schemas.EnrollmentResponse)
def get_course_enrollment(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    enrollment = db.query(models.Enrollment).filter(
        models.Enrollment.student_id == current_user["user_id"],
        models.Enrollment.course_id == course_id
    ).first()
    
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not enrolled in this course"
        )
    
    return enrollment

# ==================== LESSON PROGRESS ENDPOINTS ====================

@app.post("/progress", response_model=schemas.LessonProgressResponse, status_code=status.HTTP_201_CREATED)
def create_lesson_progress(
    progress: schemas.LessonProgressCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    # Verify enrollment
    enrollment = db.query(models.Enrollment).filter(
        models.Enrollment.id == progress.enrollment_id,
        models.Enrollment.student_id == current_user["user_id"]
    ).first()
    
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment not found"
        )
    
    # Check if progress already exists
    existing = db.query(models.LessonProgress).filter(
        models.LessonProgress.enrollment_id == progress.enrollment_id,
        models.LessonProgress.lesson_id == progress.lesson_id
    ).first()
    
    if existing:
        return existing
    
    db_progress = models.LessonProgress(**progress.dict())
    db.add(db_progress)
    db.commit()
    db.refresh(db_progress)
    return db_progress

@app.put("/progress/{progress_id}", response_model=schemas.LessonProgressResponse)
def update_lesson_progress(
    progress_id: int,
    progress_update: schemas.LessonProgressUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    progress = db.query(models.LessonProgress).filter(
        models.LessonProgress.id == progress_id
    ).first()
    
    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Progress not found"
        )
    
    # Verify ownership
    enrollment = db.query(models.Enrollment).filter(
        models.Enrollment.id == progress.enrollment_id,
        models.Enrollment.student_id == current_user["user_id"]
    ).first()
    
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    for key, value in progress_update.dict(exclude_unset=True).items():
        setattr(progress, key, value)
    
    if progress_update.is_completed and not progress.completed_at:
        progress.completed_at = datetime.utcnow()
        
        # Update enrollment progress
        enrollment.completed_lessons += 1
        if enrollment.total_lessons > 0:
            enrollment.progress_percentage = (enrollment.completed_lessons / enrollment.total_lessons) * 100
        
        # Check if course is completed
        if enrollment.completed_lessons >= enrollment.total_lessons and enrollment.total_lessons > 0:
            enrollment.status = models.EnrollmentStatus.COMPLETED
            enrollment.completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(progress)
    return progress

@app.get("/enrollments/{enrollment_id}/progress", response_model=List[schemas.LessonProgressResponse])
def get_enrollment_progress(
    enrollment_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    # Verify enrollment
    enrollment = db.query(models.Enrollment).filter(
        models.Enrollment.id == enrollment_id
    ).first()
    
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment not found"
        )
    
    # Check permissions
    if current_user["role"] != "admin" and enrollment.student_id != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    progress = db.query(models.LessonProgress).filter(
        models.LessonProgress.enrollment_id == enrollment_id
    ).all()
    
    return progress

# ==================== REVIEW ENDPOINTS ====================

@app.post("/reviews", response_model=schemas.ReviewResponse, status_code=status.HTTP_201_CREATED)
def create_review(
    review: schemas.ReviewCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    # Check if enrolled
    enrollment = db.query(models.Enrollment).filter(
        models.Enrollment.student_id == current_user["user_id"],
        models.Enrollment.course_id == review.course_id
    ).first()
    
    # Check if already reviewed
    existing = db.query(models.Review).filter(
        models.Review.student_id == current_user["user_id"],
        models.Review.course_id == review.course_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already reviewed this course"
        )
    
    db_review = models.Review(
        student_id=current_user["user_id"],
        course_id=review.course_id,
        enrollment_id=enrollment.id if enrollment else None,
        rating=review.rating,
        title=review.title,
        comment=review.comment,
        is_verified=bool(enrollment)
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review

@app.get("/courses/{course_id}/reviews", response_model=List[schemas.ReviewResponse])
def get_course_reviews(
    course_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    reviews = db.query(models.Review).filter(
        models.Review.course_id == course_id
    ).offset(skip).limit(limit).all()
    
    return reviews

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
