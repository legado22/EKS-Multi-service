

# Create models.py
cat > models.py << 'EOF'
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Enum, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum

class CourseLevel(str, enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class CourseStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

# Association table for course prerequisites
course_prerequisites = Table(
    'course_prerequisites',
    Base.metadata,
    Column('course_id', Integer, ForeignKey('courses.id'), primary_key=True),
    Column('prerequisite_id', Integer, ForeignKey('courses.id'), primary_key=True)
)

class Instructor(Base):
    __tablename__ = "instructors"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, index=True, nullable=False)  # References auth service
    bio = Column(Text)
    expertise = Column(String)
    years_experience = Column(Integer)
    linkedin_url = Column(String)
    github_url = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    courses = relationship("Course", back_populates="instructor")

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    slug = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text, nullable=False)
    short_description = Column(String(500))
    level = Column(Enum(CourseLevel), default=CourseLevel.BEGINNER, nullable=False)
    status = Column(Enum(CourseStatus), default=CourseStatus.DRAFT, nullable=False)
    price = Column(Float, default=0.0)
    duration_hours = Column(Integer)  # Total course duration
    instructor_id = Column(Integer, ForeignKey("instructors.id"), nullable=False)
    thumbnail_url = Column(String)
    video_intro_url = Column(String)
    is_featured = Column(Boolean, default=False)
    enrollment_count = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    instructor = relationship("Instructor", back_populates="courses")
    modules = relationship("CourseModule", back_populates="course", cascade="all, delete-orphan")
    prerequisites = relationship(
        "Course",
        secondary=course_prerequisites,
        primaryjoin=id==course_prerequisites.c.course_id,
        secondaryjoin=id==course_prerequisites.c.prerequisite_id,
        backref="required_for"
    )

class CourseModule(Base):
    __tablename__ = "course_modules"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    order = Column(Integer, nullable=False)
    duration_hours = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    course = relationship("Course", back_populates="modules")
    lessons = relationship("Lesson", back_populates="module", cascade="all, delete-orphan")

class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey("course_modules.id"), nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text)
    video_url = Column(String)
    duration_minutes = Column(Integer)
    order = Column(Integer, nullable=False)
    is_preview = Column(Boolean, default=False)  # Can be viewed without enrollment
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    module = relationship("CourseModule", back_populates="lessons")

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    slug = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text)
    icon = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
