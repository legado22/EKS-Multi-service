from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from models import EnrollmentStatus, OrderStatus

# Cart Schemas
class CartItemBase(BaseModel):
    course_id: int

class CartItemCreate(CartItemBase):
    pass

class CartItemResponse(CartItemBase):
    id: int
    cart_id: int
    added_at: datetime
    
    class Config:
        from_attributes = True

class CartResponse(BaseModel):
    id: int
    student_id: int
    items: List[CartItemResponse] = []
    created_at: datetime
    
    class Config:
        from_attributes = True

# Order Schemas
class OrderItemBase(BaseModel):
    course_id: int
    course_title: str
    price: float
    discount: float = 0.0
    final_price: float

class OrderItemResponse(OrderItemBase):
    id: int
    order_id: int
    
    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    items: List[dict]  # List of {course_id, price, title}
    discount_amount: float = 0.0
    notes: Optional[str] = None

class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    payment_id: Optional[str] = None

class OrderResponse(BaseModel):
    id: int
    order_number: str
    student_id: int
    total_amount: float
    discount_amount: float
    final_amount: float
    status: OrderStatus
    payment_id: Optional[str]
    notes: Optional[str]
    created_at: datetime
    items: List[OrderItemResponse] = []
    
    class Config:
        from_attributes = True

# Enrollment Schemas
class EnrollmentCreate(BaseModel):
    course_id: int
    order_id: Optional[int] = None

class EnrollmentUpdate(BaseModel):
    status: Optional[EnrollmentStatus] = None
    progress_percentage: Optional[float] = None

class EnrollmentResponse(BaseModel):
    id: int
    student_id: int
    course_id: int
    order_id: Optional[int]
    status: EnrollmentStatus
    progress_percentage: float
    completed_lessons: int
    total_lessons: int
    certificate_issued: bool
    certificate_url: Optional[str]
    enrolled_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    last_accessed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# Lesson Progress Schemas
class LessonProgressCreate(BaseModel):
    enrollment_id: int
    lesson_id: int

class LessonProgressUpdate(BaseModel):
    is_completed: Optional[bool] = None
    time_spent_minutes: Optional[int] = None
    last_position: Optional[int] = None

class LessonProgressResponse(BaseModel):
    id: int
    enrollment_id: int
    lesson_id: int
    is_completed: bool
    time_spent_minutes: int
    last_position: int
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# Review Schemas
class ReviewCreate(BaseModel):
    course_id: int
    rating: int = Field(..., ge=1, le=5)
    title: Optional[str] = None
    comment: Optional[str] = None

class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    title: Optional[str] = None
    comment: Optional[str] = None

class ReviewResponse(BaseModel):
    id: int
    student_id: int
    course_id: int
    rating: int
    title: Optional[str]
    comment: Optional[str]
    is_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
