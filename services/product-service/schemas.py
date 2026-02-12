from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import datetime
from models import CourseLevel, CourseStatus

# Instructor Schemas
class InstructorBase(BaseModel):
    user_id: int
    bio: Optional[str] = None
    expertise: Optional[str] = None
    years_experience: Optional[int] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None

class InstructorCreate(InstructorBase):
    pass

class InstructorUpdate(BaseModel):
    bio: Optional[str] = None
    expertise: Optional[str] = None
    years_experience: Optional[int] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    is_active: Optional[bool] = None

class InstructorResponse(InstructorBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Lesson Schemas
class LessonBase(BaseModel):
    title: str
    content: Optional[str] = None
    video_url: Optional[str] = None
    duration_minutes: Optional[int] = None
    order: int
    is_preview: bool = False

class LessonCreate(LessonBase):
    module_id: int

class LessonUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    video_url: Optional[str] = None
    duration_minutes: Optional[int] = None
    order: Optional[int] = None
    is_preview: Optional[bool] = None

class LessonResponse(LessonBase):
    id: int
    module_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Module Schemas
class ModuleBase(BaseModel):
    title: str
    description: Optional[str] = None
    order: int
    duration_hours: Optional[int] = None

class ModuleCreate(ModuleBase):
    course_id: int

class ModuleUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    order: Optional[int] = None
    duration_hours: Optional[int] = None

class ModuleResponse(ModuleBase):
    id: int
    course_id: int
    created_at: datetime
    lessons: List[LessonResponse] = []
    
    class Config:
        from_attributes = True

# Course Schemas
class CourseBase(BaseModel):
    title: str
    slug: str
    description: str
    short_description: Optional[str] = None
    level: CourseLevel = CourseLevel.BEGINNER
    price: float = 0.0
    duration_hours: Optional[int] = None
    thumbnail_url: Optional[str] = None
    video_intro_url: Optional[str] = None

class CourseCreate(CourseBase):
    instructor_id: int
    status: CourseStatus = CourseStatus.DRAFT

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    level: Optional[CourseLevel] = None
    status: Optional[CourseStatus] = None
    price: Optional[float] = None
    duration_hours: Optional[int] = None
    thumbnail_url: Optional[str] = None
    video_intro_url: Optional[str] = None
    is_featured: Optional[bool] = None

class CourseResponse(CourseBase):
    id: int
    instructor_id: int
    status: CourseStatus
    is_featured: bool
    enrollment_count: int
    rating: float
    created_at: datetime
    instructor: Optional[InstructorResponse] = None
    modules: List[ModuleResponse] = []
    
    class Config:
        from_attributes = True

class CourseListResponse(BaseModel):
    id: int
    title: str
    slug: str
    short_description: Optional[str]
    level: CourseLevel
    price: float
    duration_hours: Optional[int]
    thumbnail_url: Optional[str]
    instructor_id: int
    is_featured: bool
    enrollment_count: int
    rating: float
    
    class Config:
        from_attributes = True

# Category Schemas
class CategoryBase(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    icon: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
