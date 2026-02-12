from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional

import models
import schemas
from database import engine, get_db
from auth_middleware import verify_token, verify_admin, verify_instructor

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Execute Tech Academy - Product Service",
    description="Course and Instructor Management Service",
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
        "service": "Product Service",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# ==================== INSTRUCTOR ENDPOINTS ====================

@app.post("/instructors", response_model=schemas.InstructorResponse, status_code=status.HTTP_201_CREATED)
def create_instructor(
    instructor: schemas.InstructorCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_admin)
):
    # Check if instructor already exists
    db_instructor = db.query(models.Instructor).filter(
        models.Instructor.user_id == instructor.user_id
    ).first()
    
    if db_instructor:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Instructor profile already exists for this user"
        )
    
    db_instructor = models.Instructor(**instructor.dict())
    db.add(db_instructor)
    db.commit()
    db.refresh(db_instructor)
    return db_instructor

@app.get("/instructors", response_model=List[schemas.InstructorResponse])
def list_instructors(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    instructors = db.query(models.Instructor).filter(
        models.Instructor.is_active == True
    ).offset(skip).limit(limit).all()
    return instructors

@app.get("/instructors/{instructor_id}", response_model=schemas.InstructorResponse)
def get_instructor(instructor_id: int, db: Session = Depends(get_db)):
    instructor = db.query(models.Instructor).filter(
        models.Instructor.id == instructor_id
    ).first()
    
    if not instructor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instructor not found"
        )
    return instructor

@app.put("/instructors/{instructor_id}", response_model=schemas.InstructorResponse)
def update_instructor(
    instructor_id: int,
    instructor_update: schemas.InstructorUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_instructor)
):
    instructor = db.query(models.Instructor).filter(
        models.Instructor.id == instructor_id
    ).first()
    
    if not instructor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instructor not found"
        )
    
    # Instructors can only update their own profile, admins can update any
    if current_user["role"] != "admin" and instructor.user_id != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    for key, value in instructor_update.dict(exclude_unset=True).items():
        setattr(instructor, key, value)
    
    db.commit()
    db.refresh(instructor)
    return instructor

# ==================== COURSE ENDPOINTS ====================

@app.post("/courses", response_model=schemas.CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(
    course: schemas.CourseCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_instructor)
):
    # Check if slug already exists
    db_course = db.query(models.Course).filter(
        models.Course.slug == course.slug
    ).first()
    
    if db_course:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Course with this slug already exists"
        )
    
    db_course = models.Course(**course.dict())
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course

@app.get("/courses", response_model=List[schemas.CourseListResponse])
def list_courses(
    skip: int = 0,
    limit: int = 100,
    level: Optional[models.CourseLevel] = None,
    status: Optional[models.CourseStatus] = None,
    is_featured: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Course)
    
    if level:
        query = query.filter(models.Course.level == level)
    if status:
        query = query.filter(models.Course.status == status)
    else:
        # By default, only show published courses to public
        query = query.filter(models.Course.status == models.CourseStatus.PUBLISHED)
    if is_featured is not None:
        query = query.filter(models.Course.is_featured == is_featured)
    
    courses = query.offset(skip).limit(limit).all()
    return courses

@app.get("/courses/{course_id}", response_model=schemas.CourseResponse)
def get_course(course_id: int, db: Session = Depends(get_db)):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    return course

@app.get("/courses/slug/{slug}", response_model=schemas.CourseResponse)
def get_course_by_slug(slug: str, db: Session = Depends(get_db)):
    course = db.query(models.Course).filter(models.Course.slug == slug).first()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    return course

@app.put("/courses/{course_id}", response_model=schemas.CourseResponse)
def update_course(
    course_id: int,
    course_update: schemas.CourseUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_instructor)
):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Check permissions
    instructor = db.query(models.Instructor).filter(
        models.Instructor.id == course.instructor_id
    ).first()
    
    if current_user["role"] != "admin" and instructor.user_id != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    for key, value in course_update.dict(exclude_unset=True).items():
        setattr(course, key, value)
    
    db.commit()
    db.refresh(course)
    return course

@app.delete("/courses/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_admin)
):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    db.delete(course)
    db.commit()
    return None

# ==================== MODULE ENDPOINTS ====================

@app.post("/modules", response_model=schemas.ModuleResponse, status_code=status.HTTP_201_CREATED)
def create_module(
    module: schemas.ModuleCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_instructor)
):
    db_module = models.CourseModule(**module.dict())
    db.add(db_module)
    db.commit()
    db.refresh(db_module)
    return db_module

@app.get("/courses/{course_id}/modules", response_model=List[schemas.ModuleResponse])
def list_course_modules(course_id: int, db: Session = Depends(get_db)):
    modules = db.query(models.CourseModule).filter(
        models.CourseModule.course_id == course_id
    ).order_by(models.CourseModule.order).all()
    return modules

@app.put("/modules/{module_id}", response_model=schemas.ModuleResponse)
def update_module(
    module_id: int,
    module_update: schemas.ModuleUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_instructor)
):
    module = db.query(models.CourseModule).filter(
        models.CourseModule.id == module_id
    ).first()
    
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found"
        )
    
    for key, value in module_update.dict(exclude_unset=True).items():
        setattr(module, key, value)
    
    db.commit()
    db.refresh(module)
    return module

# ==================== LESSON ENDPOINTS ====================

@app.post("/lessons", response_model=schemas.LessonResponse, status_code=status.HTTP_201_CREATED)
def create_lesson(
    lesson: schemas.LessonCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_instructor)
):
    db_lesson = models.Lesson(**lesson.dict())
    db.add(db_lesson)
    db.commit()
    db.refresh(db_lesson)
    return db_lesson

@app.get("/modules/{module_id}/lessons", response_model=List[schemas.LessonResponse])
def list_module_lessons(module_id: int, db: Session = Depends(get_db)):
    lessons = db.query(models.Lesson).filter(
        models.Lesson.module_id == module_id
    ).order_by(models.Lesson.order).all()
    return lessons

@app.put("/lessons/{lesson_id}", response_model=schemas.LessonResponse)
def update_lesson(
    lesson_id: int,
    lesson_update: schemas.LessonUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_instructor)
):
    lesson = db.query(models.Lesson).filter(models.Lesson.id == lesson_id).first()
    
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )
    
    for key, value in lesson_update.dict(exclude_unset=True).items():
        setattr(lesson, key, value)
    
    db.commit()
    db.refresh(lesson)
    return lesson

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
