from sqlalchemy import Column, Integer, String, ForeignKey, Date, Time, DateTime, Enum, Index
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from .connection import Base

class AttendanceStatus(str, enum.Enum):
    PRESENT = "Present"
    ABSENT = "Absent"

class Branch(Base):
    __tablename__ = "branches"

    branch_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(20), unique=True, nullable=False, index=True)

    sections = relationship("Section", back_populates="branch", cascade="all, delete-orphan")

class Section(Base):
    __tablename__ = "sections"

    section_id = Column(Integer, primary_key=True, index=True)
    branch_id = Column(Integer, ForeignKey("branches.branch_id"), nullable=False)
    year = Column(Integer, nullable=False) # e.g., 1, 2, 3, 4
    section_name = Column(String(50), nullable=False) # e.g., "A", "B", "CSE-1"

    branch = relationship("Branch", back_populates="sections")
    students = relationship("Student", back_populates="section", cascade="all, delete-orphan")
    schedules = relationship("TimetableSchedule", back_populates="section", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_section_branch_year", "branch_id", "year"),
    )

class Classroom(Base):
    __tablename__ = "classrooms"

    classroom_id = Column(Integer, primary_key=True, index=True)
    room_number = Column(String(50), unique=True, nullable=False, index=True)
    esp32_hardware_uid = Column(String(100), unique=True, nullable=False, index=True)

    schedules = relationship("TimetableSchedule", back_populates="classroom", cascade="all, delete-orphan")

class Student(Base):
    __tablename__ = "students"

    student_id = Column(Integer, primary_key=True, index=True)
    reg_number = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(150), nullable=False)
    password_hash = Column(String(255), nullable=False)
    plain_password = Column(String(100), nullable=True) # For offline ESP32 validation sync
    section_id = Column(Integer, ForeignKey("sections.section_id"), nullable=False)

    section = relationship("Section", back_populates="students")
    attendance_logs = relationship("AttendanceLog", back_populates="student", cascade="all, delete-orphan")

class Teacher(Base):
    __tablename__ = "teachers"

    teacher_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    schedules = relationship("TimetableSchedule", back_populates="teacher", cascade="all, delete-orphan")

class Subject(Base):
    __tablename__ = "subjects"

    subject_id = Column(Integer, primary_key=True, index=True)
    subject_name = Column(String(150), nullable=False)
    course_code = Column(String(50), unique=True, nullable=False, index=True)

    schedules = relationship("TimetableSchedule", back_populates="subject", cascade="all, delete-orphan")

class TimetableSchedule(Base):
    __tablename__ = "timetable_schedules"

    schedule_id = Column(Integer, primary_key=True, index=True)
    classroom_id = Column(Integer, ForeignKey("classrooms.classroom_id"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("teachers.teacher_id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.subject_id"), nullable=False)
    section_id = Column(Integer, ForeignKey("sections.section_id"), nullable=False)
    day_of_week = Column(String(20), nullable=False) # Monday, Tuesday, etc.
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

    classroom = relationship("Classroom", back_populates="schedules")
    teacher = relationship("Teacher", back_populates="schedules")
    subject = relationship("Subject", back_populates="schedules")
    section = relationship("Section", back_populates="schedules")
    attendance_logs = relationship("AttendanceLog", back_populates="schedule", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_schedule_lookup", "classroom_id", "day_of_week", "start_time", "end_time"),
    )

class AttendanceLog(Base):
    __tablename__ = "attendance_logs"

    log_id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.student_id"), nullable=False)
    schedule_id = Column(Integer, ForeignKey("timetable_schedules.schedule_id"), nullable=False)
    date = Column(Date, nullable=False, default=datetime.utcnow().date, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    status = Column(Enum(AttendanceStatus), nullable=False, default=AttendanceStatus.PRESENT)

    student = relationship("Student", back_populates="attendance_logs")
    schedule = relationship("TimetableSchedule", back_populates="attendance_logs")

    __table_args__ = (
        Index("idx_attendance_student_date", "student_id", "date"),
        Index("idx_attendance_schedule_date", "schedule_id", "date"),
    )
